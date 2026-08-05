from __future__ import annotations

"""PySide6 Playbook page for ContractIQ Phase 2."""

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

from contract_review_assistant.branding import PRODUCT_NAME
from contract_review_assistant.clauses import ClauseLibraryService, ClauseRecord, ClauseSearchFilters
from contract_review_assistant.playbooks import (
    CLAUSE_REQUIREMENT_LEVELS,
    PLAYBOOK_STATUSES,
    RISK_TOLERANCES,
    PlaybookChecklistItem,
    PlaybookClauseRule,
    PlaybookLibraryService,
    PlaybookRecord,
    PlaybookSearchFilters,
    PlaybookValidationError,
)


class PlaybookPage(QWidget):
    """Professional editor for contract-type-specific review playbooks."""

    def __init__(
        self,
        database_path: Path | str,
        *,
        clause_library_service: ClauseLibraryService,
        service: PlaybookLibraryService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("playbookPage")
        self.clause_library_service = clause_library_service
        self.service = service or PlaybookLibraryService(
            database_path,
            clause_library_service=clause_library_service,
        )
        self.current_playbook_id: str | None = None
        self.playbooks: list[PlaybookRecord] = []
        self.clauses: list[ClauseRecord] = []
        self.clause_rule_drafts: list[PlaybookClauseRule] = []
        self._build_ui()
        self.refresh_clause_options()
        self.refresh()

    def refresh(self) -> None:
        """Reload the playbook table from the service."""

        filters = PlaybookSearchFilters(
            query=self.search_field.text(),
            risk_tolerance=self._risk_filter_value(),
            include_archived=self.status_filter.currentText() == "All playbooks",
        )
        playbooks = self.service.search(filters)
        if self.status_filter.currentText() == "Archived":
            playbooks = [playbook for playbook in playbooks if not playbook.active]
        elif self.status_filter.currentText() == "Active":
            playbooks = [playbook for playbook in playbooks if playbook.active]
        self.playbooks = playbooks
        self.table.setRowCount(len(playbooks))
        for row, playbook in enumerate(playbooks):
            values = [
                playbook.name,
                playbook.contract_type,
                playbook.risk_tolerance,
                playbook.status,
                str(len(playbook.clause_rules)),
                str(len(playbook.checklist_items)),
                f"v{playbook.version}",
                playbook.updated_at,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.UserRole, playbook.playbook_id)
                self.table.setItem(row, col, item)
        if playbooks:
            self.table.selectRow(0)
        else:
            self.current_playbook_id = None
            self._clear_editor()

    def refresh_clause_options(self) -> None:
        """Reload Clause Library standards into the assignment selector."""

        self.clauses = self.clause_library_service.search(ClauseSearchFilters(include_archived=False))
        self.clause_selector.clear()
        if not self.clauses:
            self.clause_selector.addItem("No active clause standards available", "")
            return
        for clause in self.clauses:
            self.clause_selector.addItem(f"{clause.name} — {clause.category}", clause.clause_id)

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
        splitter.setSizes([720, 820])
        root.addWidget(splitter, 1)

    def _hero(self) -> QFrame:
        hero = QFrame()
        hero.setObjectName("playbookHero")
        layout = QVBoxLayout(hero)
        layout.setContentsMargins(22, 20, 22, 20)
        eyebrow = QLabel(f"{PRODUCT_NAME} Phase 2")
        eyebrow.setObjectName("playbookEyebrow")
        title = QLabel("Playbooks")
        title.setObjectName("playbookTitle")
        detail = QLabel(
            "Create contract-type-specific review standards by grouping Clause Library language, checklist items, and escalation guidance."
        )
        detail.setObjectName("playbookDetail")
        detail.setWordWrap(True)
        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(detail)
        return hero

    def _filters(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("playbookFilters")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        self.search_field = QLineEdit()
        self.search_field.setObjectName("playbookSearchField")
        self.search_field.setPlaceholderText("Search playbooks, contract types, checklist items, or guidance")
        self.filter_risk_tolerance = QComboBox()
        self.filter_risk_tolerance.setObjectName("playbookFilterRiskToleranceField")
        self.filter_risk_tolerance.addItems(["All tolerances", *RISK_TOLERANCES])
        self.status_filter = QComboBox()
        self.status_filter.setObjectName("playbookStatusFilter")
        self.status_filter.addItems(["Active", "Archived", "All playbooks"])
        layout.addWidget(QLabel("Search"))
        layout.addWidget(self.search_field, 1)
        layout.addWidget(QLabel("Risk Tolerance"))
        layout.addWidget(self.filter_risk_tolerance)
        layout.addWidget(QLabel("Status"))
        layout.addWidget(self.status_filter)
        self.search_field.textChanged.connect(self.refresh)
        self.filter_risk_tolerance.currentTextChanged.connect(self.refresh)
        self.status_filter.currentTextChanged.connect(self.refresh)
        return panel

    def _table_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("playbookListPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 15, 16, 16)
        heading = QLabel("Review Playbooks")
        heading.setObjectName("playbookSectionTitle")
        self.table = QTableWidget(0, 8)
        self.table.setObjectName("playbookTable")
        self.table.setHorizontalHeaderLabels([
            "Playbook",
            "Contract Type",
            "Risk Tolerance",
            "Status",
            "Clauses",
            "Checklist",
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
        panel.setObjectName("playbookEditorPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 15, 16, 16)
        layout.setSpacing(10)
        heading = QLabel("Playbook Editor")
        heading.setObjectName("playbookSectionTitle")
        layout.addWidget(heading)

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        self.name_field = QLineEdit(); self.name_field.setObjectName("playbookNameField")
        self.contract_type_field = QLineEdit(); self.contract_type_field.setObjectName("playbookContractTypeField")
        self.risk_tolerance_field = QComboBox(); self.risk_tolerance_field.setObjectName("playbookRiskToleranceField"); self.risk_tolerance_field.addItems(RISK_TOLERANCES)
        self.status_field = QComboBox(); self.status_field.setObjectName("playbookStatusField"); self.status_field.addItems(PLAYBOOK_STATUSES)
        form.addWidget(QLabel("Playbook Name"), 0, 0); form.addWidget(self.name_field, 1, 0)
        form.addWidget(QLabel("Contract Type"), 0, 1); form.addWidget(self.contract_type_field, 1, 1)
        form.addWidget(QLabel("Risk Tolerance"), 0, 2); form.addWidget(self.risk_tolerance_field, 1, 2)
        form.addWidget(QLabel("Status"), 0, 3); form.addWidget(self.status_field, 1, 3)
        layout.addLayout(form)

        layout.addWidget(QLabel("Description"))
        self.description_field = QTextEdit(); self.description_field.setObjectName("playbookDescriptionField"); self.description_field.setMinimumHeight(80)
        layout.addWidget(self.description_field)

        layout.addWidget(QLabel("Clause Standards"))
        clause_controls = QGridLayout()
        self.clause_selector = QComboBox(); self.clause_selector.setObjectName("playbookClauseStandardSelector")
        self.clause_requirement_field = QComboBox(); self.clause_requirement_field.setObjectName("playbookClauseRequirementField"); self.clause_requirement_field.addItems(CLAUSE_REQUIREMENT_LEVELS)
        self.clause_guidance_field = QTextEdit(); self.clause_guidance_field.setObjectName("playbookClauseGuidanceField"); self.clause_guidance_field.setMaximumHeight(70)
        self.add_clause_button = QPushButton("Add Clause Standard")
        self.remove_clause_button = QPushButton("Remove Clause Standard")
        clause_controls.addWidget(QLabel("Standard"), 0, 0); clause_controls.addWidget(self.clause_selector, 1, 0)
        clause_controls.addWidget(QLabel("Requirement"), 0, 1); clause_controls.addWidget(self.clause_requirement_field, 1, 1)
        clause_controls.addWidget(QLabel("Guidance"), 2, 0, 1, 2); clause_controls.addWidget(self.clause_guidance_field, 3, 0, 1, 2)
        clause_controls.addWidget(self.add_clause_button, 4, 0); clause_controls.addWidget(self.remove_clause_button, 4, 1)
        layout.addLayout(clause_controls)

        self.clause_rules_table = QTableWidget(0, 3)
        self.clause_rules_table.setObjectName("playbookClauseRulesTable")
        self.clause_rules_table.setHorizontalHeaderLabels(["Clause Standard", "Requirement", "Guidance"])
        self.clause_rules_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clause_rules_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.clause_rules_table.setMaximumHeight(150)
        self.clause_rules_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.clause_rules_table)

        layout.addWidget(QLabel("Checklist Items"))
        self.checklist_field = QTextEdit(); self.checklist_field.setObjectName("playbookChecklistField"); self.checklist_field.setMinimumHeight(90)
        self.checklist_field.setPlaceholderText(
            "One item per line: item text | Required/Optional | owner role | escalation guidance"
        )
        layout.addWidget(self.checklist_field, 1)

        actions = QHBoxLayout()
        self.new_button = QPushButton("New Playbook")
        self.save_button = QPushButton("Save Playbook")
        self.archive_button = QPushButton("Archive Playbook")
        actions.addWidget(self.new_button)
        actions.addStretch()
        actions.addWidget(self.archive_button)
        actions.addWidget(self.save_button)
        layout.addLayout(actions)

        self.new_button.clicked.connect(self._new_playbook)
        self.save_button.clicked.connect(self._save_playbook)
        self.archive_button.clicked.connect(self._archive_playbook)
        self.add_clause_button.clicked.connect(self._add_clause_rule)
        self.remove_clause_button.clicked.connect(self._remove_clause_rule)
        return panel

    def _selection_changed(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.playbooks):
            return
        self._load_playbook(self.playbooks[row])

    def _load_playbook(self, playbook: PlaybookRecord) -> None:
        self.current_playbook_id = playbook.playbook_id
        self.name_field.setText(playbook.name)
        self.contract_type_field.setText(playbook.contract_type)
        self.risk_tolerance_field.setCurrentText(playbook.risk_tolerance)
        self.status_field.setCurrentText(playbook.status)
        self.description_field.setPlainText(playbook.description)
        self.clause_rule_drafts = list(playbook.clause_rules)
        self._refresh_clause_rule_table()
        self.checklist_field.setPlainText("\n".join(_checklist_line(item) for item in playbook.checklist_items))
        self.archive_button.setEnabled(playbook.active)

    def _new_playbook(self) -> None:
        self.current_playbook_id = None
        self._clear_editor()

    def _save_playbook(self) -> None:
        try:
            if self.current_playbook_id:
                self.service.update_playbook(self.current_playbook_id, **self._editor_payload())
            else:
                created = self.service.create_playbook(**self._editor_payload())
                self.current_playbook_id = created.playbook_id
            self.refresh()
        except PlaybookValidationError as exc:
            QMessageBox.warning(self, "Playbook Validation", str(exc))

    def _archive_playbook(self) -> None:
        if not self.current_playbook_id:
            return
        self.service.archive_playbook(self.current_playbook_id)
        self.refresh()

    def _add_clause_rule(self) -> None:
        clause_id = str(self.clause_selector.currentData() or "")
        if not clause_id:
            return
        rule = PlaybookClauseRule(
            clause_id=clause_id,
            requirement_level=self.clause_requirement_field.currentText(),
            guidance=self.clause_guidance_field.toPlainText(),
        )
        self.clause_rule_drafts = [existing for existing in self.clause_rule_drafts if existing.clause_id != clause_id]
        self.clause_rule_drafts.append(rule)
        self.clause_guidance_field.clear()
        self._refresh_clause_rule_table()

    def _remove_clause_rule(self) -> None:
        row = self.clause_rules_table.currentRow()
        if row < 0:
            row = len(self.clause_rule_drafts) - 1
        if 0 <= row < len(self.clause_rule_drafts):
            self.clause_rule_drafts.pop(row)
            self._refresh_clause_rule_table()

    def _refresh_clause_rule_table(self) -> None:
        self.clause_rules_table.setRowCount(len(self.clause_rule_drafts))
        names = self._clause_name_map()
        for row, rule in enumerate(self.clause_rule_drafts):
            values = [
                names.get(rule.clause_id, rule.clause_id),
                rule.requirement_level,
                rule.guidance,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.UserRole, rule.clause_id)
                self.clause_rules_table.setItem(row, col, item)

    def _editor_payload(self) -> dict:
        return {
            "name": self.name_field.text(),
            "description": self.description_field.toPlainText(),
            "contract_type": self.contract_type_field.text(),
            "risk_tolerance": self.risk_tolerance_field.currentText(),
            "status": self.status_field.currentText(),
            "clause_rules": list(self.clause_rule_drafts),
            "checklist_items": _parse_checklist(self.checklist_field.toPlainText()),
        }

    def _clear_editor(self) -> None:
        self.name_field.clear()
        self.contract_type_field.clear()
        self.risk_tolerance_field.setCurrentText("Balanced")
        self.status_field.setCurrentText("Draft")
        self.description_field.clear()
        self.clause_rule_drafts = []
        self._refresh_clause_rule_table()
        self.checklist_field.clear()
        self.archive_button.setEnabled(False)

    def _risk_filter_value(self) -> str:
        value = self.filter_risk_tolerance.currentText()
        return "" if value == "All tolerances" else value

    def _clause_name_map(self) -> dict[str, str]:
        clauses = self.clause_library_service.search(ClauseSearchFilters(include_archived=True))
        return {clause.clause_id: f"{clause.name} — {clause.category}" for clause in clauses}


def _parse_checklist(text: str) -> list[PlaybookChecklistItem]:
    items: list[PlaybookChecklistItem] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        item_text = parts[0]
        required = True
        if len(parts) > 1 and parts[1]:
            required = parts[1].casefold() not in {"optional", "false", "no", "n"}
        owner_role = parts[2] if len(parts) > 2 else ""
        escalation = parts[3] if len(parts) > 3 else ""
        items.append(
            PlaybookChecklistItem(
                text=item_text,
                required=required,
                owner_role=owner_role,
                escalation=escalation,
            )
        )
    return items


def _checklist_line(item: PlaybookChecklistItem) -> str:
    requirement = "Required" if item.required else "Optional"
    return "|".join([item.text, requirement, item.owner_role, item.escalation]).rstrip("|")
