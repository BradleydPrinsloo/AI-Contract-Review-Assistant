from __future__ import annotations

"""Reusable lightweight chart widgets for the PySide6 desktop UI."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget


class HorizontalBarChart(QWidget):
    """Simple dependency-free horizontal bar chart for dashboard summaries."""

    def __init__(self, title: str, values: dict[str, int], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("horizontalBarChart")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        self._layout.addWidget(heading)
        self.set_values(values)

    def set_values(self, values: dict[str, int]) -> None:
        """Replace the displayed series values."""

        while self._layout.count() > 1:
            item = self._layout.takeAt(1)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not values:
            empty = QLabel("No risk data yet. Scan contracts to build the distribution.")
            empty.setObjectName("emptyStateText")
            empty.setWordWrap(True)
            self._layout.addWidget(empty)
            return

        maximum = max(values.values()) or 1
        for label, count in values.items():
            self._layout.addWidget(_bar_row(label, count, maximum))


def _bar_row(label: str, count: int, maximum: int) -> QWidget:
    row = QFrame()
    row.setObjectName("chartRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    name = QLabel(label)
    name.setObjectName("chartLabel")
    name.setFixedWidth(100)
    name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    bar = QProgressBar()
    bar.setObjectName("chartBar")
    bar.setRange(0, maximum)
    bar.setValue(count)
    bar.setTextVisible(False)
    bar.setMinimumHeight(12)

    value = QLabel(str(count))
    value.setObjectName("chartValue")
    value.setFixedWidth(32)
    value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    layout.addWidget(name)
    layout.addWidget(bar, 1)
    layout.addWidget(value)
    return row
