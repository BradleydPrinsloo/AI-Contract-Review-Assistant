from __future__ import annotations

"""Contracts workspace UI composition for ContractIQ desktop review flows."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from contract_review_assistant.branding import DECISION_SUPPORT_NOTICE, PRODUCT_NAME, PRODUCT_TAGLINE


class ContractsWorkspaceBuilder:
    """Compose the dedicated contract review workspace around an existing controller.

    The controller owns workflow behavior. This builder owns the layout, object
    names, and widget hierarchy so the Contracts module can evolve independently
    from the executive dashboard and future repository modules.
    """

    def __init__(self, controller) -> None:
        self.controller = controller

    def install(self) -> None:
        """Install a polished Contracts workspace as the controller central widget."""

        app = self.controller
        app.setStyleSheet(self._style_sheet())

        root = QWidget()
        root.setObjectName("contractsWorkspacePage")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 20, 22, 16)
        layout.setSpacing(14)

        layout.addWidget(self._workflow_panel())
        layout.addWidget(self._metrics_panel())
        layout.addWidget(self._status_strip())
        layout.addWidget(self._review_splitter(), 1)

        footer = QLabel(DECISION_SUPPORT_NOTICE)
        footer.setObjectName("contractWorkspaceFooter")
        footer.setWordWrap(True)
        layout.addWidget(footer)

        app.setCentralWidget(root)
        self._connect_actions()
        app.set_actions_enabled(False)

    def _workflow_panel(self) -> QFrame:
        app = self.controller
        panel = QFrame()
        panel.setObjectName("contractWorkflowPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        text = QVBoxLayout()
        eyebrow = QLabel(f"{PRODUCT_NAME} v2.5")
        eyebrow.setObjectName("contractsEyebrow")
        title = QLabel("Contracts Workspace")
        title.setObjectName("contractsTitle")
        subtitle = QLabel("Open, scan, review, and report from one controlled workspace.")
        subtitle.setObjectName("contractsSubtitle")
        subtitle.setWordWrap(True)
        tagline = QLabel(PRODUCT_TAGLINE.replace("\n", "  "))
        tagline.setObjectName("contractsTagline")
        tagline.setWordWrap(True)
        text.addWidget(eyebrow)
        text.addWidget(title)
        text.addWidget(subtitle)
        text.addWidget(tagline)
        header.addLayout(text, 1)

        app.status_badge = QLabel("READY")
        app.status_badge.setObjectName("contractStatusBadge")
        app.status_badge.setAlignment(Qt.AlignCenter)
        app.status_badge.setFixedWidth(126)
        header.addWidget(app.status_badge)
        layout.addLayout(header)

        steps = QGridLayout()
        steps.setHorizontalSpacing(10)
        for col, (label, detail) in enumerate(
            (
                ("1. Open", "Select PDF, DOCX, or TXT"),
                ("2. Scan", "Run OCR and clause analysis"),
                ("3. Review", "Inspect findings and summary"),
                ("4. Report", "Generate Word or PDF output"),
            )
        ):
            steps.addWidget(self._step_card(label, detail), 0, col)
        layout.addLayout(steps)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        app.open_btn = QPushButton("Open Contract")
        app.analyze_btn = QPushButton("Scan Contract")
        app.summary_btn = QPushButton("Expand Summary")
        app.repository_btn = QPushButton("Repository")
        app.docx_btn = QPushButton("Export Word")
        app.csv_btn = QPushButton("Export CSV")
        app.txt_btn = QPushButton("Export Text")
        app.about_btn = QPushButton("About")

        for button in (
            app.open_btn,
            app.analyze_btn,
            app.summary_btn,
            app.docx_btn,
            app.csv_btn,
            app.txt_btn,
            app.repository_btn,
            app.about_btn,
        ):
            actions.addWidget(button)
        app.report_action_insert_index = 3
        app.report_actions_layout = actions
        actions.addStretch()
        layout.addLayout(actions)
        return panel

    def _metrics_panel(self) -> QFrame:
        app = self.controller
        panel = QFrame()
        panel.setObjectName("contractMetricsPanel")
        cards = QGridLayout(panel)
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        app.score_frame, app.score_value, _ = app.make_card("Overall Risk", "—")
        app.rating_frame, app.rating_value, _ = app.make_card("Rating", "Not analyzed")
        app.findings_frame, app.findings_value, app.severity_value = app.make_card(
            "Total Findings", "0", "High 0  •  Medium 0  •  Low 0"
        )
        app.high_frame, app.high_value, _ = app.make_card("High Priority", "0")
        app.contract_frame, app.contract_value, _ = app.make_card("Contract", "None selected")
        for col, frame in enumerate(
            (
                app.score_frame,
                app.rating_frame,
                app.findings_frame,
                app.high_frame,
                app.contract_frame,
            )
        ):
            cards.addWidget(frame, 0, col)
        return panel

    def _status_strip(self) -> QWidget:
        app = self.controller
        strip = QWidget()
        strip.setObjectName("contractStatusStrip")
        layout = QVBoxLayout(strip)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        app.status = QLabel("Ready. Open a contract to begin.")
        app.status.setObjectName("contractProgressText")
        app.progress = QProgressBar()
        app.progress.setRange(0, 100)
        app.progress.setValue(0)
        app.progress.setTextVisible(False)
        layout.addWidget(app.status)
        layout.addWidget(app.progress)
        return strip

    def _review_splitter(self) -> QSplitter:
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("contractReviewSplitter")
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._findings_panel())
        splitter.addWidget(self._summary_panel())
        splitter.setSizes([1080, 470])
        return splitter

    def _findings_panel(self) -> QFrame:
        app = self.controller
        panel = QFrame()
        panel.setObjectName("contractFindingsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 15, 16, 16)
        layout.setSpacing(11)

        header = QHBoxLayout()
        heading = QLabel("Contract Findings")
        heading.setObjectName("contractsSectionTitle")
        app.search_box = QLineEdit()
        app.search_box.setPlaceholderText("Search findings…")
        app.search_box.setMaximumWidth(320)
        app.risk_filter = QComboBox()
        app.risk_filter.addItems(
            [
                "All risks",
                "Critical",
                "High",
                "Elevated",
                "Moderate",
                "Medium",
                "Low",
                "Protective",
                "Neutral",
                "Info",
            ]
        )
        app.risk_filter.setMaximumWidth(170)
        header.addWidget(heading)
        header.addStretch()
        header.addWidget(app.search_box)
        header.addWidget(app.risk_filter)
        layout.addLayout(header)

        app.table = QTableWidget(0, 10)
        app.table.setObjectName("contractFindingsTable")
        app.table.setHorizontalHeaderLabels(
            [
                "Phrase",
                "Category",
                "Type",
                "Risk",
                "Score",
                "Confidence",
                "Location",
                "Review Note",
                "Library Standard",
                "Context",
            ]
        )
        app.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        app.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        app.table.setAlternatingRowColors(True)
        app.table.setSortingEnabled(True)
        app.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        app.table.horizontalHeader().setStretchLastSection(True)
        app.table.verticalHeader().setVisible(False)
        layout.addWidget(app.table, 1)
        return panel

    def _summary_panel(self) -> QFrame:
        app = self.controller
        panel = QFrame()
        panel.setObjectName("contractSummaryPanel")
        panel.setMinimumWidth(430)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 15, 16, 16)
        layout.setSpacing(10)

        heading = QLabel("Executive Summary")
        heading.setObjectName("contractsSectionTitle")
        app.summary_view = QTextEdit()
        app.summary_view.setObjectName("contractExecutiveSummary")
        app.summary_view.setReadOnly(True)
        app.summary_view.setHtml(
            app.format_summary_html("Open and scan a contract to display the executive summary here.")
        )

        detail_heading = QLabel("Selected Finding")
        detail_heading.setObjectName("contractsSubsectionTitle")
        app.detail_view = QTextEdit()
        app.detail_view.setObjectName("contractFindingDetail")
        app.detail_view.setReadOnly(True)
        app.detail_view.setMaximumHeight(230)
        app.detail_view.setPlainText(
            "Select a finding row to inspect its full context and review guidance."
        )
        app.false_positive_btn = QPushButton("Mark Selected as False Positive")
        app.false_positive_btn.setEnabled(False)

        layout.addWidget(heading)
        layout.addWidget(app.summary_view, 2)
        layout.addWidget(detail_heading)
        layout.addWidget(app.detail_view, 1)
        layout.addWidget(app.false_positive_btn)
        return panel

    def _step_card(self, label: str, detail: str) -> QFrame:
        card = QFrame()
        card.setObjectName("contractStepCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(13, 10, 13, 10)
        layout.setSpacing(3)
        title = QLabel(label)
        title.setObjectName("contractStepTitle")
        helper = QLabel(detail)
        helper.setObjectName("contractStepDetail")
        helper.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(helper)
        return card

    def _connect_actions(self) -> None:
        app = self.controller
        app.open_btn.clicked.connect(app.open_contract)
        app.analyze_btn.clicked.connect(app.analyze_contract)
        app.summary_btn.clicked.connect(app.show_summary)
        app.repository_btn.clicked.connect(app.open_repository)
        app.docx_btn.clicked.connect(app.export_docx_report)
        app.csv_btn.clicked.connect(app.export_csv_report)
        app.txt_btn.clicked.connect(app.export_txt_report)
        app.about_btn.clicked.connect(app.show_about)
        app.search_box.textChanged.connect(app.apply_filters)
        app.risk_filter.currentTextChanged.connect(app.apply_filters)
        app.table.itemSelectionChanged.connect(app.show_selected_finding)
        app.false_positive_btn.clicked.connect(app.mark_false_positive)

    def _style_sheet(self) -> str:
        return """
            QWidget { background:#0b1220; color:#e5e7eb; font-size:13px; }
            QWidget#contractsWorkspacePage { background:#08111f; }
            QPushButton { background:#2563eb; color:white; border:0; border-radius:8px; padding:10px 15px; font-weight:700; }
            QPushButton:hover { background:#1d4ed8; }
            QPushButton:disabled { background:#334155; color:#94a3b8; }
            QLineEdit,QComboBox,QTableWidget,QTextEdit { background:#0f172a; border:1px solid #334155; border-radius:8px; padding:6px; }
            QHeaderView::section { background:#1e293b; padding:8px; border:0; font-weight:700; }
            QTableWidget { gridline-color:#263449; alternate-background-color:#111c30; }
            QProgressBar { background:#1e293b; border:0; border-radius:5px; min-height:10px; }
            QProgressBar::chunk { background:#3b82f6; border-radius:5px; }
            QSplitter::handle { background:#1e293b; width:3px; }
            QFrame#contractWorkflowPanel {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f2544, stop:1 #111c30);
                border:1px solid #1e3a5f; border-radius:15px;
            }
            QLabel#contractsEyebrow { color:#67e8f9; font-weight:900; letter-spacing:2px; }
            QLabel#contractsTitle { color:#f8fafc; font-size:30px; font-weight:900; }
            QLabel#contractsSubtitle { color:#dbeafe; font-size:15px; font-weight:800; }
            QLabel#contractsTagline { color:#94a3b8; }
            QLabel#contractStatusBadge {
                background:#1e293b; color:#93c5fd; border:1px solid #334155;
                border-radius:14px; padding:7px; font-weight:900;
            }
            QFrame#contractStepCard, QFrame#contractFindingsPanel, QFrame#contractSummaryPanel {
                background:#0f172a; border:1px solid #263449; border-radius:12px;
            }
            QFrame#contractStepCard { background:#111c30; }
            QLabel#contractStepTitle, QLabel#contractsSectionTitle { color:#f8fafc; font-weight:900; }
            QLabel#contractStepDetail, QLabel#contractProgressText, QLabel#contractsTagline,
            QLabel#contractWorkspaceFooter { color:#94a3b8; }
            QLabel#contractsSectionTitle { font-size:18px; }
            QLabel#contractsSubsectionTitle { color:#f8fafc; font-size:16px; font-weight:900; }
        """
