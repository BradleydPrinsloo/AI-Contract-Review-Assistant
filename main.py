from __future__ import annotations

import html
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QComboBox, QDialog, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QSplitter, QSplashScreen, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from contract_review_assistant.ai_notes import openai_summary
from contract_review_assistant.app_paths import default_exports_dir, default_repository_dir, external_or_bundled_path
from contract_review_assistant.branding import (
    APP_ICON_FILENAME,
    APP_SPLASH_FILENAME,
    DECISION_SUPPORT_NOTICE,
    PRODUCT_DESCRIPTION,
    PRODUCT_DISPLAY_NAME,
    PRODUCT_NAME,
    PRODUCT_TAGLINE,
    PRODUCT_VERSION,
    REPORT_SUMMARY_TITLE,
)
from contract_review_assistant.contracts import ContractsWorkspaceBuilder
from contract_review_assistant.keyword_library import ensure_editable_keyword_library
from contract_review_assistant.repository import load_repository_entries, record_scan, search_repository
from contract_review_assistant.risk_engine import calculate_risk_assessment
from contract_review_assistant.scanner import export_csv, export_docx, export_txt, extract_document, load_keywords, scan_chunks

APP_TITLE = PRODUCT_DISPLAY_NAME
APP_ICON_PATH = external_or_bundled_path("assets", APP_ICON_FILENAME)
APP_SPLASH_PATH = external_or_bundled_path("assets", APP_SPLASH_FILENAME)
KEYWORD_SOURCE = external_or_bundled_path("data", "keywords.json")
EXPORTS_DIR = default_exports_dir()
REPOSITORY_DIR = default_repository_dir(exports_dir=EXPORTS_DIR)
RISK_COLORS = {"critical":"#ef4444","high":"#f97316","elevated":"#f59e0b","moderate":"#eab308","medium":"#eab308","low":"#22c55e","protective":"#14b8a6","neutral":"#94a3b8","info":"#94a3b8"}


@dataclass
class ScanExecutionResult:
    source_file: str
    results: list
    risk_assessment: object
    summary_text: str


class ScanWorker(QObject):
    progress = Signal(str, int)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, source_file: str, keyword_path: Path):
        super().__init__()
        self.source_file = source_file
        self.keyword_path = keyword_path

    @Slot()
    def run(self):
        try:
            self.progress.emit("Loading rule library…", 10)
            rules = load_keywords(self.keyword_path)
            self.progress.emit("Extracting contract text…", 35)
            chunks = extract_document(self.source_file)
            self.progress.emit("Analyzing clauses…", 65)
            results = scan_chunks(chunks, rules)
            assessment = calculate_risk_assessment(results)
            self.progress.emit("Preparing review summary…", 90)
            summary = openai_summary(results, assessment)
            self.finished.emit(ScanExecutionResult(self.source_file, results, assessment, summary))
        except Exception as exc:
            self.failed.emit(str(exc))


class SummaryDialog(QDialog):
    def __init__(self, parent, summary_html: str):
        super().__init__(parent)
        self.setWindowTitle("Expanded Contract Summary")
        self.resize(760, 720)
        layout = QVBoxLayout(self)
        viewer = QTextEdit()
        viewer.setReadOnly(True)
        viewer.setHtml(summary_html)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(viewer, 1)
        layout.addWidget(close_btn, 0, Qt.AlignRight)


class RepositoryDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.setWindowTitle("Contract Repository")
        self.resize(1040, 720)
        self.entries = []
        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by contract, rating, category, phrase, or summary")
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Scanned", "Contract", "Rating", "Score", "Categories"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.details = QTextEdit(); self.details.setReadOnly(True)
        self.load_btn = QPushButton("Load Selected Analysis")
        close_btn = QPushButton("Close")
        buttons = QHBoxLayout(); buttons.addWidget(self.load_btn); buttons.addStretch(); buttons.addWidget(close_btn)
        layout.addWidget(self.search); layout.addWidget(self.table, 2); layout.addWidget(self.details, 1); layout.addLayout(buttons)
        self.search.textChanged.connect(self.refresh)
        self.table.itemSelectionChanged.connect(self.show_selection)
        self.load_btn.clicked.connect(self.load_selected)
        close_btn.clicked.connect(self.close)

    def refresh(self):
        entries = load_repository_entries(REPOSITORY_DIR, legacy_reports_dir=EXPORTS_DIR)
        self.entries = search_repository(entries, self.search.text())
        self.table.setRowCount(len(self.entries))
        for row, entry in enumerate(self.entries):
            for col, value in enumerate([entry.scanned_at, entry.source_name, entry.rating, f"{entry.risk_score}/100", ", ".join(entry.categories[:3])]):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        if self.entries: self.table.selectRow(0)
        else: self.details.setPlainText("No saved analyses matched this search.")

    def selected_entry(self):
        items = self.table.selectedItems()
        if not items: return None
        row = items[0].row()
        return self.entries[row] if 0 <= row < len(self.entries) else None

    def show_selection(self):
        entry = self.selected_entry()
        if entry is None: return
        self.details.setPlainText(f"Contract: {entry.source_name}\nScanned: {entry.scanned_at}\nRating: {entry.rating}\nRisk Score: {entry.risk_score}/100\nFindings: {entry.finding_count}\nCategories: {', '.join(entry.categories) or 'None'}\n\n{entry.summary}")
        self.load_btn.setEnabled(bool(entry.findings))

    def load_selected(self):
        entry = self.selected_entry()
        if entry and entry.findings:
            self.parent_app.load_repository_entry(entry)
            self.close()


class ContractScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1600, 980)
        if APP_ICON_PATH.exists(): self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True); REPOSITORY_DIR.mkdir(parents=True, exist_ok=True)
        self.keyword_path = ensure_editable_keyword_library(KEYWORD_SOURCE, EXPORTS_DIR / "keyword-library" / "keywords.json")
        self.current_file = None; self.results = []; self.assessment = None; self.summary = ""
        self.scan_thread = None; self.scan_worker = None
        self.repository_dialog = RepositoryDialog(self)
        self.build_ui()

    def build_ui(self):
        """Install the dedicated Contracts workspace UI."""

        ContractsWorkspaceBuilder(self).install()

    def make_card(self,label,value,detail=""):
        frame=QFrame(); frame.setStyleSheet("QFrame{background:#162033;border:1px solid #334155;border-radius:11px;}")
        box=QVBoxLayout(frame); box.setContentsMargins(13,10,13,10)
        cap=QLabel(label); cap.setStyleSheet("color:#94a3b8;font-weight:700;border:0;")
        val=QLabel(value); val.setWordWrap(True); val.setStyleSheet("font-size:20px;font-weight:900;border:0;")
        det=QLabel(detail); det.setStyleSheet("color:#94a3b8;font-size:11px;border:0;"); det.setVisible(bool(detail))
        box.addWidget(cap); box.addWidget(val); box.addWidget(det)
        return frame,val,det

    def set_actions_enabled(self, analyzed):
        self.analyze_btn.setEnabled(bool(self.current_file) and self.scan_thread is None)
        self.summary_btn.setEnabled(analyzed); self.docx_btn.setEnabled(analyzed); self.txt_btn.setEnabled(analyzed); self.csv_btn.setEnabled(bool(self.results))

    def open_contract(self):
        path,_=QFileDialog.getOpenFileName(self,"Open Contract",str(Path.home()),"Contract Files (*.pdf *.docx *.txt)")
        if not path:return
        self.current_file=path; self.contract_value.setText(Path(path).name); self.status.setText("Contract selected. Ready to scan."); self.status_badge.setText("READY"); self.progress.setValue(0)
        self.clear_results(); self.set_actions_enabled(False)

    def clear_results(self):
        self.results=[]; self.assessment=None; self.summary=""; self.table.setRowCount(0)
        self.score_value.setText("—"); self.rating_value.setText("Not analyzed"); self.findings_value.setText("0"); self.high_value.setText("0"); self.severity_value.setText("High 0  •  Medium 0  •  Low 0")
        self.summary_view.setHtml(self.format_summary_html("No analysis available.")); self.detail_view.setPlainText("Select a finding row to inspect its full context and review guidance."); self.false_positive_btn.setEnabled(False)

    def analyze_contract(self):
        if not self.current_file or self.scan_thread is not None:return
        self.open_btn.setEnabled(False); self.analyze_btn.setEnabled(False); self.status_badge.setText("ANALYZING")
        self.scan_thread=QThread(self); self.scan_worker=ScanWorker(self.current_file,self.keyword_path); self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run); self.scan_worker.progress.connect(self.update_progress); self.scan_worker.finished.connect(self.scan_complete); self.scan_worker.failed.connect(self.scan_failed)
        self.scan_worker.finished.connect(self.scan_thread.quit); self.scan_worker.failed.connect(self.scan_thread.quit); self.scan_thread.finished.connect(self.cleanup_thread); self.scan_thread.start()

    @Slot(str,int)
    def update_progress(self,message,value): self.status.setText(message); self.progress.setValue(value)

    @Slot(object)
    def scan_complete(self,result):
        self.results=result.results; self.assessment=result.risk_assessment; self.summary=result.summary_text
        self.refresh_dashboard(); self.status.setText("Analysis complete. Review findings or export a report."); self.status_badge.setText("COMPLETE"); self.progress.setValue(100)
        record_scan(self.current_file,self.results,self.assessment,self.summary,REPOSITORY_DIR); self.repository_dialog.refresh(); self.set_actions_enabled(True); self.open_btn.setEnabled(True)

    @Slot(str)
    def scan_failed(self,message):
        self.status.setText("Analysis failed."); self.status_badge.setText("ERROR"); self.progress.setValue(0); self.open_btn.setEnabled(True); self.set_actions_enabled(False); QMessageBox.critical(self,"Analysis Failed",message)

    def cleanup_thread(self):
        if self.scan_worker:self.scan_worker.deleteLater()
        if self.scan_thread:self.scan_thread.deleteLater()
        self.scan_worker=None; self.scan_thread=None; self.set_actions_enabled(self.assessment is not None)

    def refresh_dashboard(self):
        self.populate_table(); self.score_value.setText(f"{self.assessment.total_score}/100"); self.rating_value.setText(self.assessment.rating)
        self.findings_value.setText(str(len(self.results)))
        high=sum(1 for x in self.results if x.risk.casefold() in {"critical","high","elevated"}); medium=sum(1 for x in self.results if x.risk.casefold() in {"moderate","medium"}); low=sum(1 for x in self.results if x.risk.casefold() in {"low","protective","neutral","info"})
        self.high_value.setText(str(high)); self.severity_value.setText(f"High {high}  •  Medium {medium}  •  Low {low}")
        color=RISK_COLORS.get(self.assessment.rating.casefold(),"#94a3b8"); self.rating_value.setStyleSheet(f"font-size:20px;font-weight:900;border:0;color:{color};")
        self.summary_view.setHtml(self.format_summary_html(self.summary))

    def populate_table(self):
        self.table.setSortingEnabled(False); self.table.setRowCount(0)
        query=self.search_box.text().strip().casefold(); selected=self.risk_filter.currentText().casefold()
        for index,item in enumerate(self.results):
            searchable=" ".join(str(v) for v in (item.phrase,item.category,item.finding_type,item.risk,item.location,item.note,item.context)).casefold()
            if query and query not in searchable: continue
            if selected!="all risks" and item.risk.casefold()!=selected: continue
            row=self.table.rowCount(); self.table.insertRow(row)
            vals=[item.phrase,item.category,item.finding_type,item.risk,item.score,f"{item.confidence}%",item.location,item.note,item.context]
            for col,val in enumerate(vals):
                cell=QTableWidgetItem(str(val)); cell.setToolTip(str(val))
                if col==0: cell.setData(Qt.UserRole,index)
                if col==3: cell.setForeground(QColor(RISK_COLORS.get(item.risk.casefold(),"#e5e7eb")))
                self.table.setItem(row,col,cell)
        self.table.setSortingEnabled(True); self.table.resizeColumnsToContents()

    def apply_filters(self): self.populate_table()

    def selected_result_index(self):
        row=self.table.currentRow()
        if row<0:return None
        item=self.table.item(row,0)
        return item.data(Qt.UserRole) if item else None

    def show_selected_finding(self):
        index=self.selected_result_index()
        if index is None or not (0<=index<len(self.results)):
            self.false_positive_btn.setEnabled(False); return
        item=self.results[index]
        self.detail_view.setHtml(f"<h3>{html.escape(item.phrase)}</h3><p><b>Category:</b> {html.escape(item.category)}<br><b>Type:</b> {html.escape(item.finding_type)}<br><b>Risk:</b> {html.escape(item.risk)}<br><b>Confidence:</b> {item.confidence}%<br><b>Location:</b> {html.escape(item.location)}</p><p><b>Review guidance</b><br>{html.escape(item.note)}</p><p><b>Full context</b><br>{html.escape(item.context)}</p>")
        self.false_positive_btn.setEnabled(True)

    def mark_false_positive(self):
        index=self.selected_result_index()
        if index is None or not (0<=index<len(self.results)):return
        item=self.results[index]
        answer=QMessageBox.question(self,"Mark False Positive",f"Remove '{item.phrase}' from this review as a false positive?\n\nExports made after this change will exclude it.")
        if answer!=QMessageBox.Yes:return
        self.results.pop(index); self.assessment=calculate_risk_assessment(self.results); self.summary=openai_summary(self.results,self.assessment)
        self.refresh_dashboard(); self.detail_view.setPlainText("Finding removed from the current review as a false positive."); self.false_positive_btn.setEnabled(False); self.status.setText("False positive removed. Risk score and summary recalculated.")

    @staticmethod
    def format_summary_html(text):
        safe=html.escape(text or "No summary available.")
        safe=safe.replace(REPORT_SUMMARY_TITLE,f"<h2>{REPORT_SUMMARY_TITLE}</h2>").replace("Top review priorities:","<h3>Top Review Priorities</h3>").replace("Recommended actions:","<h3>Recommended Actions</h3>").replace("Disclaimer:","<h3>Disclaimer</h3>")
        lines=[]
        for line in safe.splitlines():
            stripped=line.strip()
            if not stripped or set(stripped)=={"="}: continue
            if stripped.startswith("&lt;h") or stripped.startswith("<h"): lines.append(stripped)
            elif stripped.startswith("-"): lines.append(f"<li>{stripped[1:].strip()}</li>")
            else: lines.append(f"<p>{stripped}</p>")
        return "".join(lines)

    def show_about(self):
        QMessageBox.about(self,f"About {PRODUCT_NAME}",f"<h2>{PRODUCT_NAME}</h2><p><b>Version {PRODUCT_VERSION}</b></p><p>{PRODUCT_TAGLINE}</p><p>{PRODUCT_DESCRIPTION}</p><p>{DECISION_SUPPORT_NOTICE}</p>")

    def show_summary(self): SummaryDialog(self,self.format_summary_html(self.summary)).exec()
    def open_repository(self): self.repository_dialog.refresh(); self.repository_dialog.show(); self.repository_dialog.raise_()

    def load_repository_entry(self,entry):
        from contract_review_assistant.scanner import ScanResult
        self.current_file=entry.source_file; self.results=[ScanResult(**f) for f in entry.findings]; self.assessment=calculate_risk_assessment(self.results); self.assessment.total_score=entry.risk_score; self.assessment.rating=entry.rating; self.summary=entry.summary
        self.contract_value.setText(entry.source_name); self.refresh_dashboard(); self.status.setText("Loaded saved analysis from the contract repository."); self.status_badge.setText("LOADED"); self.progress.setValue(100); self.set_actions_enabled(True)

    def export_docx_report(self):
        path,_=QFileDialog.getSaveFileName(self,"Save Word Report",str(EXPORTS_DIR/self.default_report_name("docx")),"Word Documents (*.docx)")
        if path: export_docx(self.results,self.current_file or "",path,self.assessment,self.summary)
    def export_csv_report(self):
        path,_=QFileDialog.getSaveFileName(self,"Save CSV",str(EXPORTS_DIR/self.default_report_name("csv")),"CSV Files (*.csv)")
        if path: export_csv(self.results,path,self.current_file or "",self.assessment)
    def export_txt_report(self):
        path,_=QFileDialog.getSaveFileName(self,"Save Text Report",str(EXPORTS_DIR/self.default_report_name("txt")),"Text Files (*.txt)")
        if path: export_txt(self.results,self.current_file or "",path,self.assessment,self.summary)
    @staticmethod
    def default_report_name(extension): return f"contractiq_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"


def show_startup_splash(app):
    if not APP_SPLASH_PATH.exists(): return None
    pixmap=QPixmap(str(APP_SPLASH_PATH))
    if pixmap.isNull(): return None
    splash=QSplashScreen(pixmap)
    splash.showMessage(f"{PRODUCT_NAME} {PRODUCT_VERSION}",Qt.AlignBottom | Qt.AlignCenter,QColor("#dbeafe"))
    splash.show(); app.processEvents(); return splash


def main():
    app=QApplication(sys.argv)
    if APP_ICON_PATH.exists(): app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    splash=show_startup_splash(app); window=ContractScannerApp(); window.show()
    if splash: splash.finish(window)
    raise SystemExit(app.exec())

if __name__=="__main__": main()
