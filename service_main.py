from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QIcon, QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

import main as desktop
from contract_review_assistant.application_service import ContractAnalysisService
from contract_review_assistant.reporting import build_report_html, export_report_docx


class ServiceScanWorker(QObject):
    """Qt adapter around the UI-independent contract analysis service."""

    progress = Signal(str, int)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, source_file: str, keyword_path):
        super().__init__()
        self.source_file = source_file
        self.service = ContractAnalysisService(keyword_path)

    @Slot()
    def run(self) -> None:
        try:
            analysis = self.service.analyze(
                self.source_file,
                progress=lambda message, value: self.progress.emit(message, value),
            )
            self.finished.emit(analysis)
        except Exception as exc:
            self.failed.emit(str(exc))


class ReportDialog(QDialog):
    """Professional report configuration dialog for business users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate ContractIQ Report")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        heading = QLabel("Generate ContractIQ Report")
        heading.setStyleSheet("font-size:22px;font-weight:900;")
        description = QLabel(
            "Choose the ContractIQ report audience, output format, and sections to include."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color:#94a3b8;")
        layout.addWidget(heading)
        layout.addWidget(description)

        form = QFormLayout()
        self.report_type = QComboBox()
        self.report_type.addItem("Executive Summary", "executive")
        self.report_type.addItem("Full Contract Review", "full")
        self.output_format = QComboBox()
        self.output_format.addItem("PDF Document", "pdf")
        self.output_format.addItem("Microsoft Word Document", "docx")
        form.addRow("Report type", self.report_type)
        form.addRow("Output format", self.output_format)
        layout.addLayout(form)

        options_label = QLabel("Include sections")
        options_label.setStyleSheet("font-weight:800;margin-top:8px;")
        layout.addWidget(options_label)

        self.include_summary = QCheckBox("Executive summary")
        self.include_summary.setChecked(True)
        self.include_findings = QCheckBox("Detailed findings")
        self.include_findings.setChecked(True)
        self.include_recommendations = QCheckBox("Recommended next steps")
        self.include_recommendations.setChecked(True)
        layout.addWidget(self.include_summary)
        layout.addWidget(self.include_findings)
        layout.addWidget(self.include_recommendations)

        note = QLabel(
            "Executive reports automatically emphasize the highest-priority review items."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#94a3b8;font-size:11px;margin-top:6px;")
        layout.addWidget(note)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        generate_btn = QPushButton("Generate Report")
        cancel_btn.clicked.connect(self.reject)
        generate_btn.clicked.connect(self.accept)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(generate_btn)
        layout.addLayout(buttons)

        self.report_type.currentIndexChanged.connect(self._sync_options)
        self._sync_options()

    def _sync_options(self) -> None:
        is_executive = self.report_type.currentData() == "executive"
        self.include_findings.setEnabled(not is_executive)
        if is_executive:
            self.include_findings.setChecked(False)

    def options(self) -> dict:
        return {
            "report_type": self.report_type.currentData(),
            "output_format": self.output_format.currentData(),
            "include_summary": self.include_summary.isChecked(),
            "include_findings": self.include_findings.isChecked(),
            "include_recommendations": self.include_recommendations.isChecked(),
        }


class ServiceBackedContractScannerApp(desktop.ContractScannerApp):
    """Existing dashboard backed by reusable services and professional reports."""

    def __init__(self):
        self.generate_report_btn = None
        super().__init__()
        self._install_report_workflow()
        self.set_actions_enabled(self.assessment is not None)

    def _install_report_workflow(self) -> None:
        self.summary_btn.setText("ContractIQ Summary")

        # CSV and TXT remain available in the engine for integrations, but are
        # intentionally removed from the business-user interface.
        self.docx_btn.hide()
        self.csv_btn.hide()
        self.txt_btn.hide()

        self.generate_report_btn = QPushButton("Generate Report")
        root_layout = self.centralWidget().layout()
        action_layout = root_layout.itemAt(1).layout()
        action_layout.insertWidget(
            max(0, action_layout.count() - 1), self.generate_report_btn
        )
        self.generate_report_btn.clicked.connect(self.generate_report)

    def set_actions_enabled(self, analyzed):
        super().set_actions_enabled(analyzed)
        if self.generate_report_btn is not None:
            self.generate_report_btn.setEnabled(bool(analyzed))

    def analyze_contract(self):
        if not self.current_file or self.scan_thread is not None:
            return

        self.open_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.status_badge.setText("ANALYZING")

        self.scan_thread = QThread(self)
        self.scan_worker = ServiceScanWorker(self.current_file, self.keyword_path)
        self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.progress.connect(self.update_progress)
        self.scan_worker.finished.connect(self.scan_complete)
        self.scan_worker.failed.connect(self.scan_failed)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.failed.connect(self.scan_thread.quit)
        self.scan_thread.finished.connect(self.cleanup_thread)
        self.scan_thread.start()

    def mark_false_positive(self):
        index = self.selected_result_index()
        if index is None or not (0 <= index < len(self.results)):
            return

        item = self.results[index]
        answer = QMessageBox.question(
            self,
            "Mark False Positive",
            f"Remove '{item.phrase}' from this review as a false positive?\n\n"
            "Reports generated after this change will exclude it.",
        )
        if answer != QMessageBox.Yes:
            return

        remaining = list(self.results)
        remaining.pop(index)
        service = ContractAnalysisService(self.keyword_path)
        analysis = service.reassess(self.current_file or "", remaining)

        self.results = analysis.results
        self.assessment = analysis.risk_assessment
        self.summary = analysis.summary_text
        self.refresh_dashboard()
        self.detail_view.setPlainText(
            "Finding removed from the current review as a false positive."
        )
        self.false_positive_btn.setEnabled(False)
        self.status.setText(
            "False positive removed. Risk score and summary recalculated."
        )

    def generate_report(self) -> None:
        if self.assessment is None:
            QMessageBox.information(
                self, "No Analysis", "Scan or load a contract before generating a report."
            )
            return

        dialog = ReportDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        options = dialog.options()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = (
            "contractiq_executive_brief"
            if options["report_type"] == "executive"
            else "contractiq_analysis_report"
        )
        extension = options["output_format"]
        default_path = desktop.EXPORTS_DIR / f"{prefix}_{timestamp}.{extension}"
        file_filter = (
            "PDF Documents (*.pdf)"
            if extension == "pdf"
            else "Word Documents (*.docx)"
        )
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save ContractIQ Report", str(default_path), file_filter
        )
        if not output_path:
            return

        try:
            if extension == "pdf":
                self._export_pdf(output_path, options)
            else:
                export_report_docx(
                    self.results,
                    self.current_file or "",
                    output_path,
                    self.assessment,
                    self.summary,
                    report_type=options["report_type"],
                    include_summary=options["include_summary"],
                    include_findings=options["include_findings"],
                    include_recommendations=options["include_recommendations"],
                )
            self.status.setText(f"Report generated: {Path(output_path).name}")
            QMessageBox.information(
                self,
                "Report Generated",
                f"The report was successfully saved to:\n{output_path}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Report Generation Failed", str(exc))

    def _export_pdf(self, output_path: str, options: dict) -> None:
        report_html = build_report_html(
            self.results,
            self.current_file or "",
            self.assessment,
            self.summary,
            report_type=options["report_type"],
            include_summary=options["include_summary"],
            include_findings=options["include_findings"],
            include_recommendations=options["include_recommendations"],
        )
        document = QTextDocument()
        document.setHtml(report_html)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(output_path)
        document.print_(printer)


def main() -> None:
    app = QApplication(sys.argv)
    if desktop.APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(desktop.APP_ICON_PATH)))
    splash = desktop.show_startup_splash(app)
    window = ServiceBackedContractScannerApp()
    window.show()
    if splash:
        splash.finish(window)
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
