from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import main as desktop
from contract_review_assistant.branding import PRODUCT_DISPLAY_NAME, PRODUCT_NAME, PRODUCT_VERSION
from contract_review_assistant.dashboard.metrics import build_dashboard_summary, empty_dashboard_summary
from contract_review_assistant.repository import load_repository_entries
from contract_review_assistant.ui import ClauseLibraryPage, ExecutiveDashboardPage, PlaybookPage
from service_main import ServiceBackedContractScannerApp


class VersionTwoContractPlatform(ServiceBackedContractScannerApp):
    """Version 2.5 enterprise shell around the proven contract review workspace."""

    NAV_ITEMS = (
        ("Dashboard", "Home overview for contract operations."),
        ("Contracts", "Open, scan, and review contracts."),
        ("Clause Library", "Manage clause taxonomy and approved language."),
        ("Playbooks", "Define organization-specific review standards."),
        ("Reports", "Generate executive and detailed review reports."),
        ("Repository", "Search and reopen prior contract analyses."),
        ("Settings", "Configure local application preferences."),
        ("Help", "View support and decision-support guidance."),
    )

    def __init__(self) -> None:
        super().__init__()
        self.setFont(QFont("Segoe UI", 10))
        self.setWindowTitle(f"{PRODUCT_DISPLAY_NAME} Platform — Version {PRODUCT_VERSION}")
        self.resize(1760, 1020)
        self.dashboard_page: ExecutiveDashboardPage | None = None
        self.contracts_workspace: QWidget | None = None
        self.clause_library_page: ClauseLibraryPage | None = None
        self.playbook_page: PlaybookPage | None = None
        self.bottom_status_state: QLabel | None = None
        self.bottom_status_database: QLabel | None = None
        self.bottom_status_version: QLabel | None = None
        self._install_enterprise_shell()

    def _install_enterprise_shell(self) -> None:
        self.contracts_workspace = self.takeCentralWidget()
        self.contracts_workspace.setParent(None)
        self.contracts_workspace.setObjectName("contractsWorkspacePage")

        shell = QWidget()
        shell.setObjectName("platformShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        shell_layout.addWidget(self._build_header())

        body = QWidget()
        body.setObjectName("platformBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        self.pages = QStackedWidget()
        self.pages.setObjectName("platformPages")
        self.dashboard_page = ExecutiveDashboardPage(self._dashboard_summary())
        self.dashboard_page.quickActionRequested.connect(self._dashboard_quick_action)
        self.dashboard_page.recentContractActivated.connect(self._open_dashboard_contract)
        self.dashboard_page.recentReportActivated.connect(self._open_dashboard_report)
        self.clause_library_page = ClauseLibraryPage(
            desktop.CLAUSE_LIBRARY_DB,
            service=self.clause_library_service,
        )
        self.playbook_page = PlaybookPage(
            desktop.PLAYBOOK_DB,
            clause_library_service=self.clause_library_service,
            service=self.playbook_service,
        )
        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.contracts_workspace)
        self.pages.addWidget(self.clause_library_page)
        self.pages.addWidget(self.playbook_page)
        self.pages.addWidget(self._module_page("Reports", self.NAV_ITEMS[4][1], "Generate Contract Report"))
        self.pages.addWidget(self._module_page("Repository", self.NAV_ITEMS[5][1], "Open Repository"))
        self.pages.addWidget(self._module_page("Settings", self.NAV_ITEMS[6][1], "Open Settings"))
        self.pages.addWidget(self._module_page("Help", self.NAV_ITEMS[7][1], "Open Help"))

        body_layout.addWidget(sidebar)
        body_layout.addWidget(self.pages, 1)
        shell_layout.addWidget(body, 1)
        shell_layout.addWidget(self._build_bottom_status())
        self.setCentralWidget(shell)
        self.statusBar().hide()
        self._apply_enterprise_styles()
        self._set_status("Ready")

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("platformHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(12)

        logo = QLabel(f"{PRODUCT_NAME}")
        logo.setObjectName("appHeaderLogo")
        logo.setToolTip("ContractIQ decision-support platform")
        layout.addWidget(logo)

        self.global_search = QLineEdit()
        self.global_search.setObjectName("globalSearchField")
        self.global_search.setPlaceholderText("Search contracts, clauses, playbooks, or reports")
        self.global_search.setClearButtonEnabled(True)
        self.global_search.setToolTip("Dashboard search placeholder for local contract intelligence.")
        layout.addWidget(self.global_search, 1)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setToolTip("Open application settings")
        self.settings_button.clicked.connect(lambda _checked=False: self._navigate(6))
        layout.addWidget(self.settings_button)

        self.theme_toggle = QPushButton("Dark")
        self.theme_toggle.setObjectName("themeToggleButton")
        self.theme_toggle.setCheckable(True)
        self.theme_toggle.setChecked(True)
        self.theme_toggle.setToolTip("Theme toggle. Dashboard is optimized for dark mode.")
        self.theme_toggle.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_toggle)
        return header

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("platformSidebar")
        sidebar.setFixedWidth(238)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(6)

        section = QLabel("Navigation")
        section.setObjectName("sidebarSectionLabel")
        layout.addWidget(section)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: list[QPushButton] = []
        for index, (label, description) in enumerate(self.NAV_ITEMS):
            button = QPushButton(label)
            button.setObjectName(f"nav{label.replace(' ', '')}Button")
            button.setProperty("navButton", True)
            button.setCheckable(True)
            button.setToolTip(description)
            button.clicked.connect(lambda checked=False, i=index: self._navigate(i))
            self.nav_group.addButton(button, index)
            self.nav_buttons.append(button)
            layout.addWidget(button)

        self.nav_buttons[0].setChecked(True)
        layout.addStretch()
        note = QLabel("Local-first contract intelligence\nDecision-support only")
        note.setObjectName("sidebarFootnote")
        note.setWordWrap(True)
        layout.addWidget(note)
        return sidebar

    def _build_bottom_status(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("platformBottomStatusBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(18)
        self.bottom_status_state = QLabel("Ready")
        self.bottom_status_state.setObjectName("bottomStatusReady")
        self.bottom_status_database = QLabel("Database Connected")
        self.bottom_status_database.setObjectName("bottomStatusDatabase")
        self.bottom_status_version = QLabel(f"Version {PRODUCT_VERSION}")
        self.bottom_status_version.setObjectName("bottomStatusVersion")
        layout.addWidget(self.bottom_status_state)
        layout.addWidget(self.bottom_status_database)
        layout.addStretch()
        layout.addWidget(self.bottom_status_version)
        return bar

    def _module_page(self, title: str, description: str, action_text: str) -> QWidget:
        page = QFrame()
        page.setObjectName("modulePage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(38, 32, 38, 32)
        layout.setSpacing(14)

        heading = QLabel(title)
        heading.setObjectName("moduleTitle")
        detail = QLabel(description)
        detail.setObjectName("moduleDescription")
        detail.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(detail)

        card = QFrame()
        card.setObjectName("moduleCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(12)
        module_state = QLabel("Module workspace")
        module_state.setStyleSheet("font-size:17px;font-weight:800;")
        roadmap = QLabel("Use the dashboard or sidebar to access available ContractIQ workflows.")
        roadmap.setWordWrap(True)
        roadmap.setStyleSheet("color:#64748b;")
        action = QPushButton(action_text)
        action.setMaximumWidth(240)
        action.clicked.connect(lambda _checked=False, name=title: self._module_action(name))
        card_layout.addWidget(module_state)
        card_layout.addWidget(roadmap)
        card_layout.addWidget(action)
        card_layout.addStretch()
        layout.addWidget(card, 1)
        return page

    def _navigate(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)
        label = self.NAV_ITEMS[index][0]
        self._set_status(f"Ready · {label}")
        if index == 0:
            self.refresh_executive_dashboard()
        elif index == 4 and self.assessment is not None:
            self.generate_report()
        elif index == 5:
            self.open_repository()

    def _module_action(self, module_name: str) -> None:
        if module_name == "Repository":
            self.open_repository()
        elif module_name == "Reports":
            self.generate_report()
        elif module_name == "Settings":
            self._set_status("Settings are available in a future configuration workspace.")
        elif module_name == "Help":
            self._set_status("ContractIQ is decision support only; validate all findings with qualified reviewers.")

    def _dashboard_quick_action(self, action: str) -> None:
        if action == "Scan Contract":
            self._navigate(1)
            self.open_file()
        elif action == "Open Repository":
            self._navigate(5)
        elif action == "Clause Library":
            self._navigate(2)
        elif action == "New Playbook":
            self._navigate(3)
            if self.playbook_page is not None:
                self.playbook_page._new_playbook()
        elif action == "Import Contracts":
            self._set_status("Import Contracts is a dashboard intake shortcut; use Scan Contract for single-contract intake.")

    def _open_dashboard_contract(self, scan_id: str) -> None:
        try:
            entries = load_repository_entries(desktop.REPOSITORY_DIR, legacy_reports_dir=desktop.EXPORTS_DIR)
        except Exception:
            entries = []
        match = next((entry for entry in entries if entry.scan_id == scan_id), None)
        if match is not None and match.findings:
            self.load_repository_entry(match)
            self._navigate(1)
            self._set_status(f"Opened {match.source_name}")
            return
        self._navigate(5)
        self._set_status("Open Repository to inspect the selected contract record.")

    def _open_dashboard_report(self, report_path: str) -> None:
        path = Path(report_path)
        self._set_status(f"Selected report: {path.name}")

    def _toggle_theme(self, checked: bool) -> None:
        self.theme_toggle.setText("Dark" if checked else "Light")
        self._set_status("Theme preference updated for the dashboard shell.")

    def _set_status(self, message: str) -> None:
        if self.bottom_status_state is not None:
            self.bottom_status_state.setText(message or "Ready")
        if self.bottom_status_database is not None:
            connected = desktop.REPOSITORY_DIR.exists()
            self.bottom_status_database.setText("Database Connected" if connected else "Database Initializing")
        self.statusBar().showMessage(message, 6000)

    def scan_complete(self, result):
        """Refresh dashboard KPIs after the inherited scan workflow records a result."""

        super().scan_complete(result)
        self.refresh_executive_dashboard()

    def refresh_executive_dashboard(self) -> None:
        """Reload repository-derived dashboard data into the home overview."""

        if self.dashboard_page is not None:
            self.dashboard_page.refresh(self._dashboard_summary())

    def _dashboard_summary(self):
        try:
            entries = load_repository_entries(desktop.REPOSITORY_DIR, legacy_reports_dir=desktop.EXPORTS_DIR)
        except Exception:
            return empty_dashboard_summary()
        return build_dashboard_summary(
            entries,
            exports_dir=desktop.EXPORTS_DIR,
            repository_dir=desktop.REPOSITORY_DIR,
        )

    def _apply_enterprise_styles(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + """
            QWidget#platformShell, QWidget#platformBody, QWidget#dashboardContent { background:#f3f6fb; }
            QFrame#platformHeader {
                background:#ffffff; border-bottom:1px solid #d9e2ef;
            }
            QLabel#appHeaderLogo { color:#0f172a; font-size:20px; font-weight:900; }
            QLineEdit#globalSearchField {
                background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px;
                padding:8px 12px; color:#0f172a;
            }
            QPushButton#settingsButton, QPushButton#themeToggleButton {
                background:#ffffff; border:1px solid #cbd5e1; border-radius:8px;
                padding:8px 12px; color:#0f172a; font-weight:700;
            }
            QPushButton#settingsButton:hover, QPushButton#themeToggleButton:hover { background:#eef4ff; border-color:#93c5fd; }
            QFrame#platformSidebar { background:#f8fafc; border-right:1px solid #d9e2ef; }
            QLabel#sidebarSectionLabel { color:#64748b; font-size:11px; font-weight:900; letter-spacing:1px; }
            QLabel#sidebarFootnote { color:#64748b; font-size:10px; }
            QPushButton[navButton="true"] {
                background:transparent; color:#334155; text-align:left;
                border:0; border-radius:8px; padding:11px 13px; font-weight:700;
            }
            QPushButton[navButton="true"]:hover { background:#e8f1ff; color:#0f172a; }
            QPushButton[navButton="true"]:checked { background:#dbeafe; color:#1d4ed8; }
            QFrame#platformBottomStatusBar { background:#ffffff; border-top:1px solid #d9e2ef; }
            QLabel#bottomStatusReady, QLabel#bottomStatusDatabase, QLabel#bottomStatusVersion { color:#475569; font-size:11px; }
            QLabel#dashboardEyebrow { color:#2563eb; font-size:11px; font-weight:900; letter-spacing:1px; }
            QLabel#dashboardTitle { color:#0f172a; font-size:32px; font-weight:900; }
            QLabel#dashboardSubtitle, QLabel#dashboardLoadingLabel, QLabel#mutedDashboardText, QLabel#statName,
            QLabel#dashboardRiskGaugeLabel, QLabel#riskBreakdownLabel, QLabel#activitySubtitle { color:#64748b; }
            QFrame[dashboardCard="true"], QFrame#moduleCard {
                background:#ffffff; border:1px solid #d9e2ef; border-radius:16px;
            }
            QLabel#quickActionsTitle, QLabel#statisticsTitle, QLabel#recentContractsTitle, QLabel#recentReportsTitle,
            QLabel#riskOverviewTitle, QLabel#recentActivityTitle, QLabel#moduleTitle {
                color:#0f172a; font-size:18px; font-weight:900;
            }
            QLabel#statValue { color:#0f172a; font-size:18px; font-weight:900; }
            QLabel#dashboardRiskGaugeValue { color:#1d4ed8; font-size:44px; font-weight:900; }
            QLabel#riskBreakdownValue, QLabel#activityTitle { color:#0f172a; font-weight:800; }
            QPushButton[dashboardAction="true"] {
                background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px;
                padding:10px 12px; color:#0f172a; font-weight:800; text-align:left;
            }
            QPushButton[dashboardAction="true"]:hover { background:#dbeafe; border-color:#93c5fd; color:#1d4ed8; }
            QTableWidget#recentContractsTable, QListWidget#recentReportsList {
                background:#ffffff; border:1px solid #e2e8f0; border-radius:10px;
                color:#0f172a; gridline-color:#e2e8f0; alternate-background-color:#f8fafc;
            }
            QHeaderView::section {
                background:#f1f5f9; color:#475569; border:0; border-bottom:1px solid #e2e8f0;
                padding:7px; font-weight:900;
            }
            QProgressBar#dashboardRiskGaugeBar { background:#e2e8f0; border:0; border-radius:7px; min-height:14px; }
            QProgressBar#dashboardRiskGaugeBar::chunk { background:#2563eb; border-radius:7px; }
            QFrame#modulePage { background:#f3f6fb; }
            QLabel#moduleDescription { color:#64748b; font-size:14px; }
            QWidget#clauseLibraryPage, QWidget#playbookPage { background:#f3f6fb; }
            QFrame#clauseLibraryHero, QFrame#playbookHero {
                background:#ffffff; border:1px solid #d9e2ef; border-radius:16px;
            }
            QLabel#clauseLibraryEyebrow, QLabel#playbookEyebrow { color:#2563eb; font-weight:900; letter-spacing:2px; }
            QLabel#clauseLibraryTitle, QLabel#playbookTitle { color:#0f172a; font-size:32px; font-weight:900; }
            QLabel#clauseLibraryDetail, QLabel#playbookDetail { color:#64748b; font-size:13px; }
            QFrame#clauseLibraryFilters, QFrame#clauseLibraryListPanel, QFrame#clauseEditorPanel,
            QFrame#playbookFilters, QFrame#playbookListPanel, QFrame#playbookEditorPanel {
                background:#ffffff; border:1px solid #d9e2ef; border-radius:12px;
            }
            QLabel#clauseSectionTitle, QLabel#playbookSectionTitle { color:#0f172a; font-size:18px; font-weight:900; }
            """
        )


def main() -> None:
    app = QApplication(sys.argv)
    if desktop.APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(desktop.APP_ICON_PATH)))
    splash = desktop.show_startup_splash(app)
    window = VersionTwoContractPlatform()
    window.show()
    if splash:
        splash.finish(window)
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
