from __future__ import annotations

"""ContractIQ Milestone 1 professional dashboard page."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from contract_review_assistant.dashboard.metrics import DashboardSummary, empty_dashboard_summary

RISK_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "elevated": "#d97706",
    "moderate": "#ca8a04",
    "medium": "#ca8a04",
    "low": "#16a34a",
    "protective": "#0891b2",
    "neutral": "#64748b",
    "info": "#2563eb",
    "unknown": "#64748b",
}


class ExecutiveDashboardPage(QWidget):
    """Modern dashboard surface with navigation shortcuts and repository-derived widgets."""

    quickActionRequested = Signal(str)
    recentContractActivated = Signal(str)
    recentReportActivated = Signal(str)

    def __init__(self, summary: DashboardSummary | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("executiveDashboardPage")
        self.summary = summary or empty_dashboard_summary()
        self.kpi_values: dict[str, QLabel] = {}
        self.category_breakdown_layout: QVBoxLayout | None = None
        self.activity_layout: QVBoxLayout | None = None
        self._build_ui()
        self.refresh(self.summary)

    def refresh(self, summary: DashboardSummary) -> None:
        """Refresh all dashboard widgets from a precomputed dashboard summary."""

        self.summary = summary
        self.kpi_values["contracts_scanned"].setText(str(summary.contracts_scanned))
        self.kpi_values["average_risk"].setText(f"{summary.average_risk}/100")
        self.kpi_values["critical_contracts"].setText(str(summary.critical_contracts))
        self.kpi_values["reports_generated"].setText(str(summary.reports_generated))
        self.kpi_values["database_size"].setText(summary.database_size_label)
        self.risk_gauge_value.setText(f"{summary.average_risk}")
        self.risk_gauge_bar.setValue(max(0, min(100, summary.average_risk)))
        self.dashboard_status.setText("Updated from local database")
        self._populate_recent_contracts()
        self._populate_recent_reports()
        self._populate_risk_breakdown()
        self._populate_recent_activity()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("dashboardScrollArea")
        content = QWidget()
        content.setObjectName("dashboardContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        layout.addLayout(self._dashboard_heading())

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        grid.addWidget(self._quick_actions_card(), 0, 0, 1, 1)
        grid.addWidget(self._statistics_card(), 0, 1, 1, 1)
        grid.addWidget(self._risk_overview_card(), 0, 2, 1, 1)
        grid.addWidget(self._recent_contracts_card(), 1, 0, 1, 2)
        grid.addWidget(self._recent_reports_card(), 1, 2, 1, 1)
        grid.addWidget(self._recent_activity_card(), 2, 0, 1, 3)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setRowStretch(1, 1)
        layout.addLayout(grid, 1)
        layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    def _dashboard_heading(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)
        text_stack = QVBoxLayout()
        eyebrow = QLabel("CONTRACTIQ DECISION SUPPORT")
        eyebrow.setObjectName("dashboardEyebrow")
        title = QLabel("Dashboard")
        title.setObjectName("dashboardTitle")
        subtitle = QLabel("Fast portfolio overview for scans, risk, reports, and review activity.")
        subtitle.setObjectName("dashboardSubtitle")
        subtitle.setWordWrap(True)
        text_stack.addWidget(eyebrow)
        text_stack.addWidget(title)
        text_stack.addWidget(subtitle)
        layout.addLayout(text_stack, 1)
        self.dashboard_status = QLabel("Loading dashboard…")
        self.dashboard_status.setObjectName("dashboardLoadingLabel")
        self.dashboard_status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.dashboard_status)
        return layout

    def _quick_actions_card(self) -> QFrame:
        frame, layout = self._card("quickActionsCard")
        title = self._card_title("Quick Actions", "quickActionsTitle")
        detail = self._muted_label("Start common contract-review tasks without leaving the dashboard.")
        layout.addWidget(title)
        layout.addWidget(detail)
        actions = [
            ("Scan Contract", "Open the Contracts workspace and choose a contract to scan", "quickActionScanContract"),
            ("Open Repository", "Search and reopen saved contract analyses", "quickActionOpenRepository"),
            ("Clause Library", "Manage approved and rejected clause language", "quickActionClauseLibrary"),
            ("New Playbook", "Create a contract-type review standard", "quickActionNewPlaybook"),
            ("Import Contracts", "Prepare bulk intake workflow placeholder", "quickActionImportContracts"),
        ]
        for label, tooltip, object_name in actions:
            button = QPushButton(label)
            button.setObjectName(object_name)
            button.setProperty("dashboardAction", True)
            button.setToolTip(tooltip)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, action=label: self.quickActionRequested.emit(action))
            layout.addWidget(button)
        layout.addStretch()
        return frame

    def _statistics_card(self) -> QFrame:
        frame, layout = self._card("statisticsCard")
        layout.addWidget(self._card_title("Statistics", "statisticsTitle"))
        stats = [
            ("contracts_scanned", "Contracts Scanned"),
            ("average_risk", "Average Risk Score"),
            ("critical_contracts", "Critical Contracts"),
            ("reports_generated", "Reports Generated"),
            ("database_size", "Database Size"),
        ]
        for key, label in stats:
            row = QFrame()
            row.setObjectName("dashboardStatRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            name = QLabel(label)
            name.setObjectName("statName")
            value = QLabel("—")
            value.setObjectName("statValue")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.kpi_values[key] = value
            row_layout.addWidget(name, 1)
            row_layout.addWidget(value)
            layout.addWidget(row)
        layout.addStretch()
        return frame

    def _recent_contracts_card(self) -> QFrame:
        frame, layout = self._card("recentContractsCard")
        layout.addWidget(self._card_title("Recent Contracts", "recentContractsTitle"))
        self.recent_contracts_table = QTableWidget(0, 4)
        self.recent_contracts_table.setObjectName("recentContractsTable")
        self.recent_contracts_table.setHorizontalHeaderLabels(["Name", "Risk", "Date", "Status"])
        self.recent_contracts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.recent_contracts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.recent_contracts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.recent_contracts_table.setAlternatingRowColors(True)
        self.recent_contracts_table.setSortingEnabled(True)
        self.recent_contracts_table.setFocusPolicy(Qt.StrongFocus)
        self.recent_contracts_table.setTabKeyNavigation(True)
        self.recent_contracts_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recent_contracts_table.setToolTip("Double-click a contract to reopen the saved analysis.")
        self.recent_contracts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_contracts_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recent_contracts_table.itemDoubleClicked.connect(lambda _item: self._open_selected_contract())
        self.recent_contracts_table.customContextMenuRequested.connect(self._contracts_context_menu)
        layout.addWidget(self.recent_contracts_table, 1)
        return frame

    def _recent_reports_card(self) -> QFrame:
        frame, layout = self._card("recentReportsCard")
        layout.addWidget(self._card_title("Recent Reports", "recentReportsTitle"))
        self.recent_reports_list = QListWidget()
        self.recent_reports_list.setObjectName("recentReportsList")
        self.recent_reports_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recent_reports_list.setToolTip("Recent PDF, DOCX, CSV, and TXT exports.")
        self.recent_reports_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.recent_reports_list.setWordWrap(True)
        self.recent_reports_list.itemDoubleClicked.connect(lambda _item: self._open_selected_report())
        self.recent_reports_list.customContextMenuRequested.connect(self._reports_context_menu)
        layout.addWidget(self.recent_reports_list, 1)
        return frame

    def _risk_overview_card(self) -> QFrame:
        frame, layout = self._card("riskOverviewCard")
        layout.addWidget(self._card_title("Risk Overview", "riskOverviewTitle"))
        gauge = QFrame()
        gauge.setObjectName("riskGaugeFrame")
        gauge_layout = QVBoxLayout(gauge)
        gauge_layout.setContentsMargins(0, 0, 0, 0)
        gauge_layout.setSpacing(6)
        self.risk_gauge_value = QLabel("0")
        self.risk_gauge_value.setObjectName("dashboardRiskGaugeValue")
        self.risk_gauge_value.setAlignment(Qt.AlignCenter)
        gauge_label = QLabel("Overall Average Risk")
        gauge_label.setObjectName("dashboardRiskGaugeLabel")
        gauge_label.setAlignment(Qt.AlignCenter)
        self.risk_gauge_bar = QProgressBar()
        self.risk_gauge_bar.setObjectName("dashboardRiskGaugeBar")
        self.risk_gauge_bar.setRange(0, 100)
        self.risk_gauge_bar.setTextVisible(False)
        gauge_layout.addWidget(self.risk_gauge_value)
        gauge_layout.addWidget(gauge_label)
        gauge_layout.addWidget(self.risk_gauge_bar)
        layout.addWidget(gauge)
        self.category_breakdown_layout = QVBoxLayout()
        self.category_breakdown_layout.setSpacing(5)
        layout.addLayout(self.category_breakdown_layout)
        layout.addStretch()
        return frame

    def _recent_activity_card(self) -> QFrame:
        frame, layout = self._card("recentActivityCard")
        layout.addWidget(self._card_title("Recent Activity", "recentActivityTitle"))
        timeline = QFrame()
        timeline.setObjectName("recentActivityTimeline")
        self.activity_layout = QVBoxLayout(timeline)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(8)
        layout.addWidget(timeline)
        return frame

    def _card(self, object_name: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName(object_name)
        frame.setProperty("dashboardCard", True)
        frame.setMinimumHeight(210)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        shadow = QGraphicsDropShadowEffect(frame)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 70))
        frame.setGraphicsEffect(shadow)
        return frame, layout

    def _card_title(self, text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        return label

    def _muted_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("mutedDashboardText")
        label.setWordWrap(True)
        return label

    def _populate_recent_contracts(self) -> None:
        table = self.recent_contracts_table
        table.setSortingEnabled(False)
        table.setRowCount(len(self.summary.recent_contracts))
        if not self.summary.recent_contracts:
            table.setRowCount(1)
            empty = QTableWidgetItem("No contracts scanned yet")
            empty.setToolTip("Use Scan Contract to start a review.")
            table.setItem(0, 0, empty)
            for column in range(1, 4):
                table.setItem(0, column, QTableWidgetItem("—"))
            table.setSortingEnabled(True)
            return
        for row, contract in enumerate(self.summary.recent_contracts):
            values = [contract.name, f"{contract.rating} · {contract.risk_score}/100", contract.scanned_at[:10], contract.status]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                if col == 0:
                    item.setData(Qt.UserRole, contract.scan_id)
                if col == 1:
                    item.setForeground(QColor(RISK_COLORS.get(contract.rating.casefold(), RISK_COLORS["unknown"])))
                table.setItem(row, col, item)
        table.resizeColumnsToContents()
        table.setSortingEnabled(True)

    def _populate_recent_reports(self) -> None:
        self.recent_reports_list.clear()
        if not self.summary.recent_reports:
            item = QListWidgetItem("No recent exports\nPDF, DOCX, CSV, and TXT reports will appear here.")
            item.setData(Qt.UserRole, "")
            self.recent_reports_list.addItem(item)
            return
        for report in self.summary.recent_reports:
            item = QListWidgetItem(f"{report.kind}  ·  {report.name}\n{report.exported_at}")
            item.setToolTip(report.path)
            item.setData(Qt.UserRole, report.path)
            self.recent_reports_list.addItem(item)

    def _populate_risk_breakdown(self) -> None:
        layout = self._reset_layout(self.category_breakdown_layout)
        if layout is None:
            return
        if not self.summary.risk_distribution:
            layout.addWidget(self._muted_label("No risk data yet. Scan a contract to populate the gauge."))
            return
        total = max(1, sum(self.summary.risk_distribution.values()))
        for rating, count in sorted(self.summary.risk_distribution.items(), key=lambda item: item[0].casefold()):
            row = QFrame()
            row.setObjectName("riskBreakdownRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            color = QLabel("●")
            color.setStyleSheet(f"color:{RISK_COLORS.get(rating.casefold(), RISK_COLORS['unknown'])};")
            label = QLabel(rating)
            label.setObjectName("riskBreakdownLabel")
            value = QLabel(f"{count} · {round((count / total) * 100)}%")
            value.setObjectName("riskBreakdownValue")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(color)
            row_layout.addWidget(label, 1)
            row_layout.addWidget(value)
            layout.addWidget(row)

    def _populate_recent_activity(self) -> None:
        layout = self._reset_layout(self.activity_layout)
        if layout is None:
            return
        if not self.summary.recent_activity:
            for title in ("Imported Contract", "Generated Report", "Updated Clause Library", "Created Playbook"):
                layout.addWidget(self._activity_row(title, "Waiting for local activity", "Info"))
            return
        for item in self.summary.recent_activity:
            layout.addWidget(self._activity_row(item.title, item.subtitle, item.severity))

    def _activity_row(self, title: str, subtitle: str, severity: str) -> QFrame:
        row = QFrame()
        row.setObjectName("activityTimelineRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        dot = QLabel("●")
        dot.setObjectName("activityDot")
        dot.setStyleSheet(f"color:{RISK_COLORS.get(severity.casefold(), RISK_COLORS['info'])};")
        text_stack = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("activityTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("activitySubtitle")
        subtitle_label.setWordWrap(True)
        text_stack.addWidget(title_label)
        text_stack.addWidget(subtitle_label)
        row_layout.addWidget(dot)
        row_layout.addLayout(text_stack, 1)
        return row

    def _open_selected_contract(self) -> None:
        row = self.recent_contracts_table.currentRow()
        if row < 0:
            return
        item = self.recent_contracts_table.item(row, 0)
        if item is None:
            return
        scan_id = str(item.data(Qt.UserRole) or "")
        if scan_id:
            self.recentContractActivated.emit(scan_id)

    def _open_selected_report(self) -> None:
        item = self.recent_reports_list.currentItem()
        if item is None:
            return
        path = str(item.data(Qt.UserRole) or "")
        if path:
            self.recentReportActivated.emit(path)

    def _contracts_context_menu(self, position) -> None:
        menu = QMenu(self)
        open_action = menu.addAction("Open Contract")
        repository_action = menu.addAction("Open Repository")
        chosen = menu.exec(self.recent_contracts_table.viewport().mapToGlobal(position))
        if chosen == open_action:
            self._open_selected_contract()
        elif chosen == repository_action:
            self.quickActionRequested.emit("Open Repository")

    def _reports_context_menu(self, position) -> None:
        menu = QMenu(self)
        open_action = menu.addAction("Open Report")
        chosen = menu.exec(self.recent_reports_list.viewport().mapToGlobal(position))
        if chosen == open_action:
            self._open_selected_report()

    def _reset_layout(self, layout: QVBoxLayout | None) -> QVBoxLayout | None:
        if layout is None:
            return None
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        return layout
