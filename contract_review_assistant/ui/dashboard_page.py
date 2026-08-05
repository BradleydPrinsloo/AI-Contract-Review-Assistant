from __future__ import annotations

"""ContractIQ Version 2.5 executive dashboard page."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from contract_review_assistant.branding import PRODUCT_NAME, PRODUCT_TAGLINE
from contract_review_assistant.dashboard.metrics import DashboardSummary, empty_dashboard_summary
from contract_review_assistant.ui.charts import HorizontalBarChart


class ExecutiveDashboardPage(QWidget):
    """Read-only executive KPI dashboard with no contract-scanner controls."""

    def __init__(self, summary: DashboardSummary | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("executiveDashboardPage")
        self.summary = summary or empty_dashboard_summary()
        self.kpi_values: dict[str, QLabel] = {}
        self.recent_activity_layout: QVBoxLayout | None = None
        self.recent_contracts_layout: QVBoxLayout | None = None
        self.review_statistics_layout: QVBoxLayout | None = None
        self.risk_chart: HorizontalBarChart | None = None
        self._build_ui()
        self.refresh(self.summary)

    def refresh(self, summary: DashboardSummary) -> None:
        """Refresh dashboard widgets from a precomputed summary model."""

        self.summary = summary
        self.kpi_values["total_contracts"].setText(str(summary.total_contracts))
        self.kpi_values["average_risk"].setText(f"{summary.average_risk}/100")
        self.kpi_values["awaiting_review"].setText(str(summary.contracts_awaiting_review))
        self.kpi_values["high_risk"].setText(str(summary.high_risk_contracts))
        self.kpi_values["last_30_days"].setText(str(summary.contracts_last_30_days))
        self.kpi_values["completion_rate"].setText(f"{summary.completion_rate}%")
        if self.risk_chart is not None:
            self.risk_chart.set_values(summary.risk_distribution)
        self._populate_recent_activity()
        self._populate_recent_contracts()
        self._populate_review_statistics()

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
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)

        layout.addWidget(self._hero())
        layout.addLayout(self._kpi_grid())

        lower = QGridLayout()
        lower.setHorizontalSpacing(16)
        lower.setVerticalSpacing(16)
        lower.addWidget(self._risk_distribution_card(), 0, 0)
        lower.addWidget(self._recent_contracts_card(), 0, 1)
        lower.addWidget(self._review_statistics_card(), 1, 0)
        lower.addWidget(self._recent_activity_card(), 1, 1)
        lower.setColumnStretch(0, 1)
        lower.setColumnStretch(1, 1)
        layout.addLayout(lower, 1)
        layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    def _hero(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardHero")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(8)

        eyebrow = QLabel(f"{PRODUCT_NAME} v2.5")
        eyebrow.setObjectName("dashboardEyebrow")
        title = QLabel("Executive Dashboard")
        title.setObjectName("dashboardTitle")
        subtitle = QLabel(PRODUCT_TAGLINE.replace("\n", "  "))
        subtitle.setObjectName("dashboardSubtitle")
        subtitle.setWordWrap(True)
        context = QLabel(
            "Portfolio-level contract intelligence: review load, risk movement, recent contract activity, "
            "and decision-ready operational KPIs. Scanner controls live in the Contracts workspace."
        )
        context.setObjectName("dashboardContext")
        context.setWordWrap(True)

        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(context)
        return frame

    def _kpi_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        cards = [
            ("total_contracts", "Total Contracts", "All repository records"),
            ("average_risk", "Average Risk", "Portfolio weighted score"),
            ("awaiting_review", "Contracts Awaiting Review", "Risk-bearing scans"),
            ("high_risk", "High Risk Contracts", "Critical / high / elevated"),
            ("last_30_days", "Contracts This Month", "Scanned in last 30 days"),
            ("completion_rate", "Review Completion", "Ready until formal workflow states"),
        ]
        for index, (key, title, detail) in enumerate(cards):
            grid.addWidget(self._kpi_card(key, title, detail), index // 3, index % 3)
        return grid

    def _kpi_card(self, key: str, title: str, detail: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardKpiCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(7)
        label = QLabel(title)
        label.setObjectName("kpiLabel")
        value = QLabel("—")
        value.setObjectName("kpiValue")
        helper = QLabel(detail)
        helper.setObjectName("kpiHelper")
        helper.setWordWrap(True)
        layout.addWidget(label)
        layout.addWidget(value)
        layout.addWidget(helper)
        self.kpi_values[key] = value
        return frame

    def _risk_distribution_card(self) -> QFrame:
        frame, layout = self._section_card()
        self.risk_chart = HorizontalBarChart("Risk Distribution", self.summary.risk_distribution)
        layout.addWidget(self.risk_chart)
        return frame

    def _recent_contracts_card(self) -> QFrame:
        frame, layout = self._section_card("Recent Contracts")
        self.recent_contracts_layout = layout
        return frame

    def _review_statistics_card(self) -> QFrame:
        frame, layout = self._section_card("Review Statistics")
        self.review_statistics_layout = layout
        return frame

    def _recent_activity_card(self) -> QFrame:
        frame, layout = self._section_card("Recent Activity")
        self.recent_activity_layout = layout
        return frame

    def _section_card(self, title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("dashboardSectionCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        if title:
            heading = QLabel(title)
            heading.setObjectName("sectionTitle")
            layout.addWidget(heading)
        return frame, layout

    def _populate_recent_contracts(self) -> None:
        layout = self._reset_dynamic_layout(self.recent_contracts_layout, keep=1)
        if layout is None:
            return
        if not self.summary.recent_contracts:
            layout.addWidget(self._empty_label("No contracts scanned yet. Use the Contracts workspace to begin."))
            return
        for contract in self.summary.recent_contracts:
            categories = ", ".join(contract.categories) if contract.categories else "No categories"
            layout.addWidget(
                self._row_card(
                    contract.name,
                    f"{contract.rating} · {contract.risk_score}/100 · {contract.finding_count} findings",
                    categories,
                )
            )

    def _populate_recent_activity(self) -> None:
        layout = self._reset_dynamic_layout(self.recent_activity_layout, keep=1)
        if layout is None:
            return
        if not self.summary.recent_activity:
            layout.addWidget(self._empty_label("Recent scan and report activity will appear here."))
            return
        for item in self.summary.recent_activity:
            layout.addWidget(self._row_card(item.title, item.subtitle, item.severity))

    def _populate_review_statistics(self) -> None:
        layout = self._reset_dynamic_layout(self.review_statistics_layout, keep=1)
        if layout is None:
            return
        stats = [
            ("Average Risk", f"{self.summary.average_risk}/100"),
            ("Contracts Awaiting Review", str(self.summary.contracts_awaiting_review)),
            ("High Risk Contracts", str(self.summary.high_risk_contracts)),
            ("Review Completion", f"{self.summary.completion_rate}%"),
        ]
        for label, value in stats:
            row = QFrame()
            row.setObjectName("statRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            name = QLabel(label)
            name.setObjectName("statName")
            score = QLabel(value)
            score.setObjectName("statValue")
            score.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(name, 1)
            row_layout.addWidget(score)
            layout.addWidget(row)

    def _row_card(self, title: str, subtitle: str, detail: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("dashboardRowCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)
        heading = QLabel(title)
        heading.setObjectName("rowTitle")
        text = QLabel(subtitle)
        text.setObjectName("rowSubtitle")
        text.setWordWrap(True)
        helper = QLabel(detail)
        helper.setObjectName("rowDetail")
        helper.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(text)
        layout.addWidget(helper)
        return frame

    def _empty_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("emptyStateText")
        label.setWordWrap(True)
        return label

    def _reset_dynamic_layout(self, layout: QVBoxLayout | None, *, keep: int) -> QVBoxLayout | None:
        if layout is None:
            return None
        while layout.count() > keep:
            item = layout.takeAt(keep)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        return layout
