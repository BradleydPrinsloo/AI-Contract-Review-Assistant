from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from contract_review_assistant.ai_notes import openai_summary
from contract_review_assistant.app_paths import (
    default_exports_dir,
    default_repository_dir,
    external_or_bundled_path,
)
from contract_review_assistant.keyword_library import ensure_editable_keyword_library
from contract_review_assistant.repository import (
    load_repository_entries,
    record_scan,
    search_repository,
)
from contract_review_assistant.risk_engine import calculate_risk_assessment
from contract_review_assistant.scanner import (
    export_csv,
    export_docx,
    export_txt,
    extract_document,
    load_keywords,
    scan_chunks,
)

APP_TITLE = "AI Contract Scanner"
APP_ICON_PATH = external_or_bundled_path("assets", "ai_contract_scanner.ico")
KEYWORD_SOURCE = external_or_bundled_path("data", "keywords.json")
EXPORTS_DIR = default_exports_dir()
REPOSITORY_DIR = default_repository_dir(exports_dir=EXPORTS_DIR)

RISK_COLORS = {
    "critical": "#ef4444",
    "high": "#f97316",
    "elevated": "#f59e0b",
    "moderate": "#eab308",
    "medium": "#eab308",
    "low": "#22c55e",
    "protective": "#14b8a6",
    "neutral": "#94a3b8",
    "info": "#94a3b8",
}


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
            self.finished.emit(
                ScanExecutionResult(self.source_file, results, assessment, summary)
            )
        except Exception as exc:
            self.failed.emit(str(exc))


class RepositoryDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.setWindowTitle("Contract Repository")
        self.resize(1040, 720)
        self.entries = []

        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Search by contract, rating, category, phrase, or summary"
        )
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Scanned", "Contract", "Rating", "Score", "Categories"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.load_btn = QPushButton("Load Selected Analysis")
        close_btn = QPushButton("Close")

        buttons = QHBoxLayout()
        buttons.addWidget(self.load_btn)
        buttons.addStretch()
        buttons.addWidget(close_btn)

        layout.addWidget(self.search)
        layout.addWidget(self.table, 2)
        layout.addWidget(self.details, 1)
        layout.addLayout(buttons)

        self.search.textChanged.connect(self.refresh)
        self.table.itemSelectionChanged.connect(self.show_selection)
        self.load_btn.clicked.connect(self.load_selected)
        close_btn.clicked.connect(self.close)

    def refresh(self):
        entries = load_repository_entries(
            REPOSITORY_DIR, legacy_reports_dir=EXPORTS_DIR
        )
        self.entries = search_repository(entries, self.search.text())
        self.table.setRowCount(len(self.entries))
        for row, entry in enumerate(self.entries):
            values = [
                entry.scanned_at,
                entry.source_name,
                entry.rating,
                f"{entry.risk_score}/100",
                ", ".join(entry.categories[:3]),
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        if self.entries:
            self.table.selectRow(0)
        else:
            self.details.setPlainText("No saved analyses matched this search.")

    def selected_entry(self):
        items = self.table.selectedItems()
        if not items:
            return None
        row = items[0].row()
        return self.entries[row] if 0 <= row < len(self.entries) else None

    def show_selection(self):
        entry = self.selected_entry()
        if entry is None:
            return
        self.details.setPlainText(
            f"Contract: {entry.source_name}\n"
            f"Scanned: {entry.scanned_at}\n"
            f"Rating: {entry.rating}\n"
            f"Risk Score: {entry.risk_score}/100\n"
            f"Findings: {entry.finding_count}\n"
            f"Categories: {', '.join(entry.categories) or 'None'}\n\n"
            f"{entry.summary}"
        )
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
        self.resize(1560, 960)
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))

        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        REPOSITORY_DIR.mkdir(parents=True, exist_ok=True)
        self.keyword_path = ensure_editable_keyword_library(
            KEYWORD_SOURCE, EXPORTS_DIR / "keyword-library" / "keywords.json"
        )

        self.current_file: str | None = None
        self.results = []
        self.assessment = None
        self.summary = ""
        self.scan_thread = None
        self.scan_worker = None
        self.repository_dialog = RepositoryDialog(self)
        self.build_ui()

    def build_ui(self):
        self.setStyleSheet(
            """
            QWidget { background:#0b1220; color:#e5e7eb; font-size:13px; }
            QPushButton { background:#2563eb; color:white; border:0; border-radius:8px; padding:10px 15px; font-weight:700; }
            QPushButton:hover { background:#1d4ed8; }
            QPushButton:disabled { background:#334155; color:#94a3b8; }
            QLineEdit, QComboBox, QTableWidget, QTextEdit {
                background:#0f172a; border:1px solid #334155; border-radius:8px; padding:6px;
            }
            QComboBox::drop-down { border:0; width:24px; }
            QHeaderView::section { background:#1e293b; padding:8px; border:0; font-weight:700; }
            QTableWidget { gridline-color:#263449; alternate-background-color:#111c30; }
            QProgressBar { background:#1e293b; border:0; border-radius:5px; min-height:10px; }
            QProgressBar::chunk { background:#3b82f6; border-radius:5px; }
            QSplitter::handle { background:#1e293b; width:2px; }
            """
        )

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header_text = QVBoxLayout()
        title = QLabel("AI Contract Scanner")
        title.setStyleSheet("font-size:30px; font-weight:900;")
        subtitle = QLabel(
            "Professional contract analysis with rule-based scoring, OCR fallback, reports, and optional AI-assisted summaries."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#94a3b8; font-size:14px;")
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addLayout(header_text, 1)
        self.status_badge = QLabel("READY")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setFixedWidth(120)
        self.status_badge.setStyleSheet(
            "background:#1e293b; color:#93c5fd; border:1px solid #334155; border-radius:14px; padding:7px; font-weight:800;"
        )
        header.addWidget(self.status_badge)
        layout.addLayout(header)

        actions = QHBoxLayout()
        self.open_btn = QPushButton("Open Contract")
        self.analyze_btn = QPushButton("Analyze Contract")
        self.summary_btn = QPushButton("Open Summary")
        self.repository_btn = QPushButton("Repository")
        self.docx_btn = QPushButton("Export Word")
        self.csv_btn = QPushButton("Export CSV")
        self.txt_btn = QPushButton("Export Text")
        for button in (
            self.open_btn,
            self.analyze_btn,
            self.summary_btn,
            self.repository_btn,
            self.docx_btn,
            self.csv_btn,
            self.txt_btn,
        ):
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        self.score_frame, self.score_value = self.make_card("Overall Risk", "—")
        self.rating_frame, self.rating_value = self.make_card("Rating", "Not analyzed")
        self.findings_frame, self.findings_value = self.make_card("Total Findings", "0")
        self.high_frame, self.high_value = self.make_card("High Priority", "0")
        self.contract_frame, self.contract_value = self.make_card("Contract", "None selected")
        cards.addWidget(self.score_frame, 0, 0)
        cards.addWidget(self.rating_frame, 0, 1)
        cards.addWidget(self.findings_frame, 0, 2)
        cards.addWidget(self.high_frame, 0, 3)
        cards.addWidget(self.contract_frame, 0, 4)
        layout.addLayout(cards)

        self.status = QLabel("Ready. Open a contract to begin.")
        self.status.setStyleSheet("color:#cbd5e1; font-weight:600;")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        findings_panel = QFrame()
        findings_panel.setStyleSheet(
            "QFrame { background:#0f172a; border:1px solid #263449; border-radius:10px; }"
        )
        findings_layout = QVBoxLayout(findings_panel)
        findings_header = QHBoxLayout()
        heading = QLabel("Contract Findings")
        heading.setStyleSheet("font-size:18px; font-weight:900; border:0;")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search findings…")
        self.search_box.setMaximumWidth(300)
        self.risk_filter = QComboBox()
        self.risk_filter.addItems(
            ["All risks", "Critical", "High", "Elevated", "Moderate", "Medium", "Low", "Protective", "Neutral", "Info"]
        )
        self.risk_filter.setMaximumWidth(160)
        findings_header.addWidget(heading)
        findings_header.addStretch()
        findings_header.addWidget(self.search_box)
        findings_header.addWidget(self.risk_filter)
        findings_layout.addLayout(findings_header)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["Phrase", "Category", "Type", "Risk", "Score", "Confidence", "Location", "Review Note", "Context"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        findings_layout.addWidget(self.table, 1)

        summary_panel = QFrame()
        summary_panel.setMinimumWidth(390)
        summary_panel.setStyleSheet(
            "QFrame { background:#0f172a; border:1px solid #263449; border-radius:10px; }"
        )
        summary_layout = QVBoxLayout(summary_panel)
        summary_heading = QLabel("Executive Summary")
        summary_heading.setStyleSheet("font-size:18px; font-weight:900; border:0;")
        self.summary_view = QTextEdit()
        self.summary_view.setReadOnly(True)
        self.summary_view.setPlainText(
            "Open and analyze a contract to display the executive summary, review priorities, and recommendations here."
        )
        self.summary_view.setStyleSheet("line-height:1.4;")
        summary_layout.addWidget(summary_heading)
        summary_layout.addWidget(self.summary_view, 1)

        splitter.addWidget(findings_panel)
        splitter.addWidget(summary_panel)
        splitter.setSizes([1080, 420])
        layout.addWidget(splitter, 1)

        footer = QLabel(
            "Decision-support tool only. Results require qualified human review and do not constitute legal advice."
        )
        footer.setStyleSheet("color:#94a3b8;")
        layout.addWidget(footer)
        self.setCentralWidget(root)

        self.open_btn.clicked.connect(self.open_contract)
        self.analyze_btn.clicked.connect(self.analyze_contract)
        self.summary_btn.clicked.connect(self.show_summary)
        self.repository_btn.clicked.connect(self.open_repository)
        self.docx_btn.clicked.connect(self.export_docx_report)
        self.csv_btn.clicked.connect(self.export_csv_report)
        self.txt_btn.clicked.connect(self.export_txt_report)
        self.search_box.textChanged.connect(self.apply_filters)
        self.risk_filter.currentTextChanged.connect(self.apply_filters)
        self.set_actions_enabled(False)

    def make_card(self, label: str, value: str) -> tuple[QFrame, QLabel]:
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background:#162033; border:1px solid #334155; border-radius:11px; }"
        )
        box = QVBoxLayout(frame)
        box.setContentsMargins(13, 10, 13, 10)
        caption = QLabel(label)
        caption.setStyleSheet("color:#94a3b8; font-weight:700; border:0;")
        value_label = QLabel(value)
        value_label.setWordWrap(True)
        value_label.setStyleSheet("font-size:20px; font-weight:900; border:0;")
        box.addWidget(caption)
        box.addWidget(value_label)
        return frame, value_label

    def set_actions_enabled(self, analyzed: bool):
        self.analyze_btn.setEnabled(bool(self.current_file) and self.scan_thread is None)
        self.summary_btn.setEnabled(analyzed)
        self.docx_btn.setEnabled(analyzed)
        self.txt_btn.setEnabled(analyzed)
        self.csv_btn.setEnabled(bool(self.results))

    def open_contract(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Contract",
            str(Path.home()),
            "Contract Files (*.pdf *.docx *.txt)",
        )
        if not path:
            return
        self.current_file = path
        self.contract_value.setText(Path(path).name)
        self.status.setText("Contract selected. Ready to analyze.")
        self.status_badge.setText("READY")
        self.progress.setValue(0)
        self.clear_results()
        self.set_actions_enabled(False)

    def clear_results(self):
        self.results = []
        self.assessment = None
        self.summary = ""
        self.table.setRowCount(0)
        self.score_value.setText("—")
        self.rating_value.setText("Not analyzed")
        self.findings_value.setText("0")
        self.high_value.setText("0")
        self.summary_view.setPlainText(
            "Analyze the selected contract to display the executive summary and recommendations."
        )
        self.update_risk_visuals(None)

    def analyze_contract(self):
        if not self.current_file or self.scan_thread is not None:
            return
        self.open_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.status_badge.setText("ANALYZING")
        self.scan_thread = QThread(self)
        self.scan_worker = ScanWorker(self.current_file, self.keyword_path)
        self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.progress.connect(self.update_progress)
        self.scan_worker.finished.connect(self.scan_complete)
        self.scan_worker.failed.connect(self.scan_failed)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.failed.connect(self.scan_thread.quit)
        self.scan_thread.finished.connect(self.cleanup_thread)
        self.scan_thread.start()

    @Slot(str, int)
    def update_progress(self, message: str, value: int):
        self.status.setText(message)
        self.progress.setValue(value)

    @Slot(object)
    def scan_complete(self, result: ScanExecutionResult):
        self.results = result.results
        self.assessment = result.risk_assessment
        self.summary = result.summary_text
        self.populate_table()
        self.update_dashboard()
        self.status.setText("Analysis complete. Review findings or export a report.")
        self.status_badge.setText("COMPLETE")
        self.progress.setValue(100)
        record_scan(
            self.current_file,
            self.results,
            self.assessment,
            self.summary,
            REPOSITORY_DIR,
        )
        self.repository_dialog.refresh()
        self.set_actions_enabled(True)
        self.open_btn.setEnabled(True)

    @Slot(str)
    def scan_failed(self, message: str):
        self.status.setText("Analysis failed.")
        self.status_badge.setText("ERROR")
        self.progress.setValue(0)
        self.open_btn.setEnabled(True)
        self.set_actions_enabled(False)
        QMessageBox.critical(self, "Analysis Failed", message)

    def cleanup_thread(self):
        if self.scan_worker:
            self.scan_worker.deleteLater()
        if self.scan_thread:
            self.scan_thread.deleteLater()
        self.scan_worker = None
        self.scan_thread = None
        self.set_actions_enabled(self.assessment is not None)

    def update_dashboard(self):
        if self.assessment is None:
            return
        self.score_value.setText(f"{self.assessment.total_score}/100")
        self.rating_value.setText(self.assessment.rating)
        self.findings_value.setText(str(self.assessment.finding_count))
        high_count = sum(
            1
            for item in self.results
            if str(item.risk).casefold() in {"high", "critical"}
        )
        self.high_value.setText(str(high_count))
        self.summary_view.setPlainText(self.summary or "No summary available.")
        self.update_risk_visuals(self.assessment.rating)

    def update_risk_visuals(self, rating: str | None):
        color = RISK_COLORS.get(str(rating or "neutral").casefold(), "#64748b")
        self.score_frame.setStyleSheet(
            f"QFrame {{ background:#162033; border:2px solid {color}; border-radius:11px; }}"
        )
        self.rating_frame.setStyleSheet(
            f"QFrame {{ background:#162033; border:2px solid {color}; border-radius:11px; }}"
        )
        self.rating_value.setStyleSheet(
            f"font-size:20px; font-weight:900; color:{color}; border:0;"
        )

    def populate_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.results))
        for row, item in enumerate(self.results):
            values = [
                item.phrase,
                item.category,
                item.finding_type,
                item.risk,
                item.score,
                f"{item.confidence}%",
                item.location,
                item.note,
                item.context,
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setToolTip(str(value))
                if col == 3:
                    color = RISK_COLORS.get(str(value).casefold())
                    if color:
                        cell.setForeground(QColor(color))
                self.table.setItem(row, col, cell)
        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)
        self.apply_filters()

    def apply_filters(self):
        query = self.search_box.text().strip().casefold()
        risk = self.risk_filter.currentText().strip().casefold()
        for row in range(self.table.rowCount()):
            row_text = " ".join(
                self.table.item(row, col).text()
                for col in range(self.table.columnCount())
                if self.table.item(row, col) is not None
            ).casefold()
            row_risk = (
                self.table.item(row, 3).text().casefold()
                if self.table.item(row, 3)
                else ""
            )
            matches_query = not query or query in row_text
            matches_risk = risk == "all risks" or row_risk == risk
            self.table.setRowHidden(row, not (matches_query and matches_risk))

    def show_summary(self):
        QMessageBox.information(
            self,
            "Contract Analysis Summary",
            self.summary or "No summary available.",
        )

    def open_repository(self):
        self.repository_dialog.refresh()
        self.repository_dialog.show()
        self.repository_dialog.raise_()

    def load_repository_entry(self, entry):
        from contract_review_assistant.scanner import ScanResult

        self.current_file = entry.source_file
        self.results = [ScanResult(**finding) for finding in entry.findings]
        self.assessment = calculate_risk_assessment(self.results)
        self.assessment.total_score = entry.risk_score
        self.assessment.rating = entry.rating
        self.summary = entry.summary
        self.contract_value.setText(entry.source_name)
        self.populate_table()
        self.update_dashboard()
        self.status.setText("Loaded saved analysis from the contract repository.")
        self.status_badge.setText("LOADED")
        self.progress.setValue(100)
        self.set_actions_enabled(True)

    def export_docx_report(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Word Report",
            str(EXPORTS_DIR / self.default_report_name("docx")),
            "Word Documents (*.docx)",
        )
        if path:
            export_docx(
                self.results,
                self.current_file or "",
                path,
                self.assessment,
                self.summary,
            )

    def export_csv_report(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            str(EXPORTS_DIR / self.default_report_name("csv")),
            "CSV Files (*.csv)",
        )
        if path:
            export_csv(
                self.results,
                path,
                self.current_file or "",
                self.assessment,
            )

    def export_txt_report(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Text Report",
            str(EXPORTS_DIR / self.default_report_name("txt")),
            "Text Files (*.txt)",
        )
        if path:
            export_txt(
                self.results,
                self.current_file or "",
                path,
                self.assessment,
                self.summary,
            )

    @staticmethod
    def default_report_name(extension: str) -> str:
        return f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"


def main():
    app = QApplication(sys.argv)
    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    window = ContractScannerApp()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
