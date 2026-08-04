from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

import main as desktop
from contract_review_assistant.application_service import ContractAnalysisService


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


class ServiceBackedContractScannerApp(desktop.ContractScannerApp):
    """Existing dashboard backed by the reusable application service."""

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
            "Exports made after this change will exclude it.",
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


def main() -> None:
    app = QApplication(sys.argv)
    if desktop.APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(desktop.APP_ICON_PATH)))
    window = ServiceBackedContractScannerApp()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
