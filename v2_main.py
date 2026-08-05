from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import main as desktop
from contract_review_assistant.branding import PRODUCT_DISPLAY_NAME, PRODUCT_NAME, PRODUCT_VERSION
from contract_review_assistant.dashboard.metrics import build_dashboard_summary, empty_dashboard_summary
from contract_review_assistant.repository import load_repository_entries
from contract_review_assistant.ui import ClauseLibraryPage, ExecutiveDashboardPage
from service_main import ServiceBackedContractScannerApp


class VersionTwoContractPlatform(ServiceBackedContractScannerApp):
    """Version 2.5 enterprise shell around the proven contract review workspace."""

    NAV_ITEMS = (
        ("Dashboard", "Executive operational overview and contract portfolio KPIs."),
        ("Contracts", "Open, scan, and review contracts."),
        ("Repository", "Search and reopen prior contract analyses."),
        ("Clause Library", "Manage clause taxonomy and approved language."),
        ("Playbooks", "Define organization-specific review standards."),
        ("Compliance", "Evaluate contracts against policy requirements."),
        ("Analytics", "Track risk trends, review volume, and outcomes."),
        ("Reports", "Generate executive and detailed review reports."),
        ("Administration", "Configure users, integrations, and platform settings."),
    )

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{PRODUCT_DISPLAY_NAME} Platform — Version {PRODUCT_VERSION}")
        self.resize(1760, 1020)
        self.dashboard_page: ExecutiveDashboardPage | None = None
        self.contracts_workspace: QWidget | None = None
        self.clause_library_page: ClauseLibraryPage | None = None
        self._install_enterprise_shell()

    def _install_enterprise_shell(self) -> None:
        self.contracts_workspace = self.takeCentralWidget()
        self.contracts_workspace.setParent(None)
        self.contracts_workspace.setObjectName("contractsWorkspacePage")

        shell = QWidget()
        shell.setObjectName("platformShell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        self.pages = QStackedWidget()
        self.pages.setObjectName("platformPages")
        self.dashboard_page = ExecutiveDashboardPage(self._dashboard_summary())
        self.clause_library_page = ClauseLibraryPage(
            desktop.CLAUSE_LIBRARY_DB,
            service=self.clause_library_service,
        )
        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.contracts_workspace)
        self.pages.addWidget(self._module_page("Repository", self.NAV_ITEMS[2][1], "Open Repository"))
        self.pages.addWidget(self.clause_library_page)
        self.pages.addWidget(self._module_page("Playbooks", self.NAV_ITEMS[4][1], "Create First Playbook"))
        self.pages.addWidget(self._module_page("Compliance", self.NAV_ITEMS[5][1], "Configure Compliance Rules"))
        self.pages.addWidget(self._module_page("Analytics", self.NAV_ITEMS[6][1], "View Analytics Roadmap"))
        self.pages.addWidget(self._module_page("Reports", self.NAV_ITEMS[7][1], "Generate Contract Report"))
        self.pages.addWidget(self._module_page("Administration", self.NAV_ITEMS[8][1], "Open Platform Settings"))

        shell_layout.addWidget(sidebar)
        shell_layout.addWidget(self.pages, 1)
        self.setCentralWidget(shell)

        self.setStyleSheet(
            self.styleSheet()
            + """
            QWidget#platformShell { background:#080f1d; }
            QFrame#platformSidebar { background:#0a1324; border-right:1px solid #263449; }
            QLabel#platformBrand { font-size:20px; font-weight:900; color:#f8fafc; }
            QLabel#platformVersion { color:#60a5fa; font-size:11px; font-weight:800; }
            QPushButton[navButton="true"] {
                background:transparent; color:#cbd5e1; text-align:left;
                border:0; border-radius:8px; padding:11px 13px; font-weight:700;
            }
            QPushButton[navButton="true"]:hover { background:#162033; color:white; }
            QPushButton[navButton="true"]:checked { background:#1d4ed8; color:white; }
            QWidget#dashboardContent { background:#080f1d; }
            QFrame#dashboardHero {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f2544, stop:1 #111c30);
                border:1px solid #1e3a5f; border-radius:16px;
            }
            QLabel#dashboardEyebrow { color:#67e8f9; font-weight:900; letter-spacing:2px; }
            QLabel#dashboardTitle { font-size:34px; font-weight:900; color:#f8fafc; }
            QLabel#dashboardSubtitle { color:#dbeafe; font-size:18px; font-weight:800; }
            QLabel#dashboardContext { color:#94a3b8; font-size:13px; }
            QFrame#dashboardKpiCard, QFrame#dashboardSectionCard {
                background:#0f172a; border:1px solid #263449; border-radius:14px;
            }
            QLabel#kpiLabel, QLabel#kpiHelper, QLabel#rowSubtitle, QLabel#rowDetail,
            QLabel#emptyStateText, QLabel#chartLabel, QLabel#statName { color:#94a3b8; }
            QLabel#kpiValue { font-size:28px; font-weight:900; color:#f8fafc; }
            QLabel#sectionTitle { font-size:18px; font-weight:900; color:#f8fafc; }
            QFrame#dashboardRowCard { background:#111c30; border:1px solid #1f3048; border-radius:10px; }
            QLabel#rowTitle { color:#e5e7eb; font-weight:900; }
            QLabel#statValue, QLabel#chartValue { color:#f8fafc; font-weight:900; }
            QProgressBar#chartBar { background:#1e293b; border:0; border-radius:6px; min-height:12px; }
            QProgressBar#chartBar::chunk { background:#38bdf8; border-radius:6px; }
            QFrame#modulePage { background:#0b1220; }
            QLabel#moduleTitle { font-size:30px; font-weight:900; color:#f8fafc; }
            QLabel#moduleDescription { color:#94a3b8; font-size:14px; }
            QFrame#moduleCard { background:#111c30; border:1px solid #263449; border-radius:12px; }
            QWidget#clauseLibraryPage { background:#080f1d; }
            QFrame#clauseLibraryHero {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #10223d, stop:1 #111c30);
                border:1px solid #1e3a5f; border-radius:16px;
            }
            QLabel#clauseLibraryEyebrow { color:#67e8f9; font-weight:900; letter-spacing:2px; }
            QLabel#clauseLibraryTitle { color:#f8fafc; font-size:32px; font-weight:900; }
            QLabel#clauseLibraryDetail { color:#94a3b8; font-size:13px; }
            QFrame#clauseLibraryFilters, QFrame#clauseLibraryListPanel, QFrame#clauseEditorPanel {
                background:#0f172a; border:1px solid #263449; border-radius:12px;
            }
            QLabel#clauseSectionTitle { color:#f8fafc; font-size:18px; font-weight:900; }
            """
        )

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("platformSidebar")
        sidebar.setFixedWidth(235)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(6)

        brand = QLabel(PRODUCT_NAME)
        brand.setObjectName("platformBrand")
        version = QLabel(f"PLATFORM V2.5 · {PRODUCT_VERSION}")
        version.setObjectName("platformVersion")
        layout.addWidget(brand)
        layout.addWidget(version)
        layout.addSpacing(18)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: list[QPushButton] = []

        for index, (label, _description) in enumerate(self.NAV_ITEMS):
            button = QPushButton(label)
            button.setProperty("navButton", True)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self._navigate(i))
            self.nav_group.addButton(button, index)
            self.nav_buttons.append(button)
            layout.addWidget(button)

        self.nav_buttons[0].setChecked(True)
        layout.addStretch()

        status = QLabel(f"{PRODUCT_NAME} local-first intelligence\nDecision-support platform")
        status.setWordWrap(True)
        status.setStyleSheet("color:#64748b;font-size:10px;")
        layout.addWidget(status)
        return sidebar

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

        module_state = QLabel("Version 2.5 module foundation")
        module_state.setStyleSheet("font-size:17px;font-weight:800;")
        roadmap = QLabel(
            "This module is part of the enterprise navigation architecture. "
            "Its production workflow will be implemented in the next Version 2.5 milestones."
        )
        roadmap.setWordWrap(True)
        roadmap.setStyleSheet("color:#94a3b8;")
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

        if index == 0:
            self.refresh_executive_dashboard()
        elif index == 2:
            self.open_repository()
        elif index == 7 and self.assessment is not None:
            self.generate_report()

    def _module_action(self, module_name: str) -> None:
        if module_name == "Repository":
            self.open_repository()
        elif module_name == "Reports":
            self.generate_report()
        elif module_name in {"Playbooks", "Compliance", "Analytics", "Administration"}:
            self.statusBar().showMessage(
                f"{module_name} is scheduled for the next Version 2.5 development milestone.",
                6000,
            )

    def scan_complete(self, result):
        """Refresh executive KPIs after the inherited scan workflow records a result."""

        super().scan_complete(result)
        self.refresh_executive_dashboard()

    def refresh_executive_dashboard(self) -> None:
        """Reload repository-derived dashboard data into the executive overview."""

        if self.dashboard_page is not None:
            self.dashboard_page.refresh(self._dashboard_summary())

    def _dashboard_summary(self):
        try:
            entries = load_repository_entries(desktop.REPOSITORY_DIR, legacy_reports_dir=desktop.EXPORTS_DIR)
        except Exception:
            return empty_dashboard_summary()
        return build_dashboard_summary(entries)


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
