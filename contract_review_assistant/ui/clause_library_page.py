from __future__ import annotations

"""PySide6 Clause Library page for ContractIQ Phase 2."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from contract_review_assistant.clauses import (
    RISK_LEVELS,
    ClauseLibraryService,
    ClauseRecord,
    ClauseSearchFilters,
    ClauseValidationError,
)
from contract_review_assistant.branding import PRODUCT_NAME


class ClauseLibraryPage(QWidget):
    """Professional clause editor for company-standard contract language."""

    def __init__(
        self,
        database_path: Path | str,
        *,
        service: ClauseLibraryService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("clauseLibraryPage")
        self.service = service or ClauseLibraryService(database_path)
        self.current_clause_id: str | None = None
        self.clauses: list[ClauseRecord] = []
        self._build_ui()
        self.refresh()

    def refresh(self) -> None:
        """Reload the table from the clause-library service."""

        filters = ClauseSearchFilters(
            query=self.search_field.text(),
            risk_level=self._risk_filter_value(),
            include_archived=self.status_filter.currentText() == "All clauses",
        )
        clauses = self.service.search(filters)
        if self.status_filter.currentText() == "Archived":
            clauses = [clause for clause in clauses if not clause.active]
        elif self.status_filter.currentText() == "Active":
            clauses = [clause for clause in clauses if clause.active]
        self.clauses = clauses
        self.table.setRowCount(len(clauses))
        for row, clause in enumerate(clauses):
            values = [
                clause.name,
                clause.category,
                clause.risk_level,
                "Active" if clause.active else "Archived",
                f"v{clause.version}",
                clause.updated_at,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.UserRole, clause.clause_id)
                self.table.setItem(row, col, item)
        if clauses:
            self.table.selectRow(0)
        else:
            self.current_clause_id = None
            self._clear_editor()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(34, 30, 34, 30)
        root.setSpacing(16)
        root.addWidget(self._hero())
        root.addWidget(self._filters())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._table_panel())
        splitter.addWidget(self._editor_panel())
        splitter.setSizes([700, 760])
        root.addWidget(splitter, 1)

    def _hero(self) -> QFrame:
        hero = QFrame()
        hero.setObjectName("clauseLibraryHero")
        layout = QVBoxLayout(hero)
        layout.setContentsMargins(22, 20, 22, 20)
        eyebrow = QLabel(f"{PRODUCT_NAME} Phase 2")
        eyebrow.setObjectName("clauseLibraryEyebrow")
        title = QLabel("Clause Library")
        title.setObjectName("clauseLibraryTitle")
        detail = QLabel(
            "Manage approved company wording, rejected wording, examples, risk levels, and explanation notes before playbooks and compliance rules consume them."
        )
        detail.setObjectName("clauseLibraryDetail")
        detail.setWordWrap(True)
        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(detail)
        return hero

    def _filters(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("clauseLibraryFilters")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        self.search_field = QLineEdit()
        self.search_field.setObjectName("clauseSearchField")
        self.search_field.setPlaceholderText("Search clauses, wording, examples, or explanations")
        self.filter_risk = QComboBox()
        self.filter_risk.setObjectName("clauseFilterRiskField")
        self.filter_risk.addItems(["All risks", *RISK_LEVELS])
        self.status_filter = QComboBox()
        self.status_filter.setObjectName("clauseStatusFilter")
        self.status_filter.addItems(["Active", "Archived", "All clauses"])
        layout.addWidget(QLabel("Search"))
        layout.addWidget(self.search_field, 1)
        layout.addWidget(QLabel("Risk"))
        layout.addWidget(self.filter_risk)
        layout.addWidget(QLabel("Status"))
        layout.addWidget(self.status_filter)
        self.search_field.textChanged.connect(self.refresh)
        self.filter_risk.currentTextChanged.connect(self.refresh)
        self.status_filter.currentTextChanged.connect(self.refresh)
        return panel

    def _table_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("clauseLibraryListPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 15, 16, 16)
        heading = QLabel("Clause Standards")
        heading.setObjectName("clauseSectionTitle")
        self.table = QTableWidget(0, 6)
        self.table.setObjectName("clauseLibraryTable")
        self.table.setHorizontalHeaderLabels([
            "Clause",
            "Category",
            "Risk",
            "Status",
            "Version",
            "Updated",
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(heading)
        layout.addWidget(self.table, 1)
        return panel

    def _editor_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("clauseEditorPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 15, 16, 16)
        layout.setSpacing(10)
        heading = QLabel("Clause Editor")
        heading.setObjectName("clauseSectionTitle")
        layout.addWidget(heading)

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        self.name_field = QLineEdit(); self.name_field.setObjectName("clauseNameField")
        self.category_field = QLineEdit(); self.category_field.setObjectName("clauseCategoryField")
        self.risk_field = QComboBox(); self.risk_field.setObjectName("clauseRiskField"); self.risk_field.addItems(RISK_LEVELS)
        form.addWidget(QLabel("Clause Name"), 0, 0); form.addWidget(self.name_field, 1, 0)
        form.addWidget(QLabel("Category"), 0, 1); form.addWidget(self.category_field, 1, 1)
        form.addWidget(QLabel("Risk Level"), 0, 2); form.addWidget(self.risk_field, 1, 2)
        layout.addLayout(form)

        layout.addWidget(QLabel("Company Wording"))
        self.company_wording = QTextEdit(); self.company_wording.setObjectName("clauseCompanyWordingField"); self.company_wording.setMinimumHeight(95)
        layout.addWidget(self.company_wording)
        layout.addWidget(QLabel("Rejected Wording"))
        self.rejected_wording = QTextEdit(); self.rejected_wording.setObjectName("clauseRejectedWordingField"); self.rejected_wording.setMinimumHeight(80)
        layout.addWidget(self.rejected_wording)
        layout.addWidget(QLabel("Examples"))
        self.examples_field = QTextEdit(); self.examples_field.setObjectName("clauseExamplesField"); self.examples_field.setMaximumHeight(80)
        layout.addWidget(self.examples_field)
        layout.addWidget(QLabel("AI Explanation"))
        self.explanation_field = QTextEdit(); self.explanation_field.setObjectName("clauseExplanationField"); self.explanation_field.setMinimumHeight(90)
        layout.addWidget(self.explanation_field, 1)

        actions = QHBoxLayout()
        self.new_button = QPushButton("New Clause")
        self.save_button = QPushButton("Save Clause")
        self.archive_button = QPushButton("Archive Clause")
        self.explain_button = QPushButton("Explain Clause")
        actions.addWidget(self.new_button)
        actions.addStretch()
        actions.addWidget(self.archive_button)
        actions.addWidget(self.explain_button)
        actions.addWidget(self.save_button)
        layout.addLayout(actions)
        self.new_button.clicked.connect(self._new_clause)
        self.save_button.clicked.connect(self._save_clause)
        self.archive_button.clicked.connect(self._archive_clause)
        self.explain_button.clicked.connect(self._explain_clause)
        return panel

    def _selection_changed(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.clauses):
            return
        self._load_clause(self.clauses[row])

    def _load_clause(self, clause: ClauseRecord) -> None:
        self.current_clause_id = clause.clause_id
        self.name_field.setText(clause.name)
        self.category_field.setText(clause.category)
        self.risk_field.setCurrentText(clause.risk_level)
        self.company_wording.setPlainText(clause.company_wording)
        self.rejected_wording.setPlainText(clause.rejected_wording)
        self.examples_field.setPlainText("\n".join(clause.examples))
        self.explanation_field.setPlainText(clause.ai_explanation)
        self.archive_button.setEnabled(clause.active)

    def _new_clause(self) -> None:
        self.current_clause_id = None
        self._clear_editor()

    def _save_clause(self) -> None:
        try:
            if self.current_clause_id:
                self.service.update_clause(self.current_clause_id, **self._editor_payload())
            else:
                self.service.create_clause(**self._editor_payload())
            self.refresh()
        except ClauseValidationError as exc:
            QMessageBox.warning(self, "Clause Validation", str(exc))

    def _archive_clause(self) -> None:
        if not self.current_clause_id:
            return
        self.service.archive_clause(self.current_clause_id)
        self.refresh()

    def _explain_clause(self) -> None:
        if not self.current_clause_id:
            return
        clause = self.service.explain_clause(self.current_clause_id)
        self._load_clause(clause)
        self.refresh()

    def _editor_payload(self) -> dict:
        return {
            "name": self.name_field.text(),
            "category": self.category_field.text(),
            "risk_level": self.risk_field.currentText(),
            "company_wording": self.company_wording.toPlainText(),
            "rejected_wording": self.rejected_wording.toPlainText(),
            "examples": self.examples_field.toPlainText().splitlines(),
            "ai_explanation": self.explanation_field.toPlainText(),
        }

    def _clear_editor(self) -> None:
        self.name_field.clear()
        self.category_field.clear()
        self.risk_field.setCurrentText("Medium")
        self.company_wording.clear()
        self.rejected_wording.clear()
        self.examples_field.clear()
        self.explanation_field.clear()
        self.archive_button.setEnabled(False)

    def _risk_filter_value(self) -> str:
        value = self.filter_risk.currentText()
        return "" if value == "All risks" else value
