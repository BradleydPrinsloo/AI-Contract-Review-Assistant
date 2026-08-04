from __future__ import annotations

import sys

from PySide6.QtCore import Qt
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
from service_main import ServiceBackedContractScannerApp


class VersionTwoContractPlatform(ServiceBackedContractScannerApp):
    """Version 2 enterprise shell around the proven contract review workspace."""

    NAV_ITEMS = (
        ("Dashboard", "Operational overview and current contract review."),
        ("Contracts", "Open, analyze, and review contracts."),
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
        self.setWindowTitle("Contract Intelligence Platform — Version 2")
        self.resize(1760, 1020)
        self._install_enterprise_shell()

    def _install_enterprise_shell(self) -> None:
        dashboard = self.takeCentralWidget()
        dashboard.setParent(None)

        shell = QWidget()
        shell.setObjectName("platformShell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        self.pages = QStackedWidget()
        self.pages.setObjectName("platformPages")
        self.pages.addWidget(dashboard)

        # Contracts intentionally opens the same proven workspace for now.
        self.pages.addWidget(dashboard)
        self.pages.addWidget(self._module_page("Repository", self.NAV_ITEMS[2][1], "Open Repository"))
        self.pages.addWidget(self._module_page("Clause Library", self.NAV_ITEMS[3][1], "Build Clause Library"))
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
            QPushButton[navButton="true"]:checked {
                background:#1d4ed8; color:white;
            }
            QFrame#modulePage { background:#0b1220; }
            QLabel#moduleTitle { font-size:30px; font-weight:900; color:#f8fafc; }
            QLabel#moduleDescription { color:#94a3b8; font-size:14px; }
            QFrame#moduleCard { background:#111c30; border:1px solid #263449; border-radius:12px; }
            """
        )

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("platformSidebar")
        sidebar.setFixedWidth(235)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(6)

        brand = QLabel("Contract Intelligence")
        brand.setObjectName("platformBrand")
        version = QLabel("PLATFORM V2")
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

        status = QLabel("Local-first contract intelligence\nDecision-support platform")
        status.setWordWrap(True)
        status.setStyleSheet("color:#64748b;font-size:10px;line-height:1.4;")
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

        module_state = QLabel("Version 2 module foundation")
        module_state.setStyleSheet("font-size:17px;font-weight:800;")
        roadmap = QLabel(
            "This module is now part of the enterprise navigation architecture. "
            "Its production workflow will be implemented in the next Version 2 milestones."
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
        # Dashboard and Contracts share the current contract workspace during
        # the first V2 milestone. Independent pages follow in later slices.
        page_index = 0 if index in {0, 1} else index
        self.pages.setCurrentIndex(page_index)

        if index == 2:
            self.open_repository()
        elif index == 7 and self.assessment is not None:
            self.generate_report()

    def _module_action(self, module_name: str) -> None:
        if module_name == "Repository":
            self.open_repository()
        elif module_name == "Reports":
            self.generate_report()
        elif module_name in {"Clause Library", "Playbooks", "Compliance", "Analytics", "Administration"}:
            self.statusBar().showMessage(
                f"{module_name} is scheduled for the next Version 2 development milestone.",
                6000,
            )


def main() -> None:
    app = QApplication(sys.argv)
    if desktop.APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(desktop.APP_ICON_PATH)))
    window = VersionTwoContractPlatform()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
