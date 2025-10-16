from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class SummarizePage(QtWidgets.QWidget):
    summarizeRequested = QtCore.Signal(str, int)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.input_edit = QtWidgets.QPlainTextEdit()
        self.spin = QtWidgets.QSpinBox()
        self.btn = QtWidgets.QPushButton("要約")
        self.progress = QtWidgets.QProgressBar()
        self.output_edit = QtWidgets.QPlainTextEdit()
        self._build_ui()

    def _build_ui(self) -> None:
        self.input_edit.setPlaceholderText("原文をここに貼り付け...")

        self.spin.setRange(1, 20)
        self.spin.setValue(3)
        self.spin.setPrefix("最大文数: ")

        self.progress.setRange(0, 0)
        self.progress.setVisible(False)

        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("ここに要約が表示されます")

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.spin)
        top.addStretch(1)
        top.addWidget(self.btn)
        top.addWidget(self.progress)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("原文"))
        layout.addWidget(self.input_edit, 2)
        layout.addLayout(top)
        layout.addWidget(QtWidgets.QLabel("要約"))
        layout.addWidget(self.output_edit, 3)

        self.btn.clicked.connect(self._handle_click)

    def _handle_click(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            QtWidgets.QMessageBox.information(self, "情報", "原文が空です。")
            return

        self.output_edit.clear()
        self.set_busy(True)
        self.summarizeRequested.emit(text, self.spin.value())

    def set_busy(self, busy: bool) -> None:
        self.btn.setEnabled(not busy)
        self.progress.setVisible(busy)

    def show_result(self, payload: str) -> None:
        self.output_edit.setPlainText(payload)

    def show_error(self, message: str) -> None:
        self.output_edit.setPlainText(f"[ERROR] {message}")
