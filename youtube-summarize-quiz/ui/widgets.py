from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class QAItem(QtWidgets.QWidget):
    """Accordion-like widget displaying a question and its answer."""

    def __init__(self, question: str, answer: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.btn = QtWidgets.QToolButton()
        self.btn.setText(question)
        self.btn.setCheckable(True)
        self.btn.setChecked(False)
        self.btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.btn.setArrowType(QtCore.Qt.RightArrow)

        self.ans = QtWidgets.QLabel(answer)
        self.ans.setWordWrap(True)
        self.ans.setVisible(False)

        self.btn.toggled.connect(self._toggle)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.addWidget(self.btn)
        layout.addWidget(self.ans)

    def _toggle(self, on: bool) -> None:
        self.ans.setVisible(on)
        self.btn.setArrowType(QtCore.Qt.DownArrow if on else QtCore.Qt.RightArrow)


def clear_layout(layout: QtWidgets.QLayout) -> None:
    """Remove all widgets from *layout* safely."""

    while layout.count():
        item = layout.takeAt(0)
        if item is None:
            continue
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
