from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ui.widgets import QAItem, clear_layout


class YouTubeSummarizePage(QtWidgets.QWidget):
    urlSubmitted = QtCore.Signal(str)
    summarizeRequested = QtCore.Signal()
    quizRequested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.url_edit = QtWidgets.QLineEdit()
        self.url_btn = QtWidgets.QPushButton("登録")
        self.summarize_btn = QtWidgets.QPushButton("要約開始")
        self.quiz_btn = QtWidgets.QPushButton("クイズ生成")
        self.quiz_progress = QtWidgets.QProgressBar()
        self.quiz_scroll = QtWidgets.QScrollArea()
        self.quiz_container = QtWidgets.QWidget()
        self.quiz_layout = QtWidgets.QVBoxLayout(self.quiz_container)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        self.url_edit.setPlaceholderText("YouTubeのURLを入力してください")

        self.url_btn.clicked.connect(self._on_url_clicked)
        self.summarize_btn.clicked.connect(self._on_summarize_clicked)
        self.quiz_btn.clicked.connect(self._on_quiz_clicked)

        self.quiz_progress.setRange(0, 0)
        self.quiz_progress.setVisible(False)

        btn_layout = QtWidgets.QVBoxLayout()
        btn_layout.addWidget(self.url_btn, 1)
        btn_layout.addWidget(self.summarize_btn, 1)
        btn_layout.addWidget(self.quiz_btn, 1)
        btn_layout.addWidget(self.quiz_progress, 1)

        spx = QtWidgets.QSizePolicy.Expanding
        spy = QtWidgets.QSizePolicy.Expanding
        self.url_edit.setSizePolicy(spx, spy)
        self.url_btn.setSizePolicy(spx, spy)
        self.summarize_btn.setSizePolicy(spx, spy)
        self.quiz_btn.setSizePolicy(spx, spy)

        two_btn_h = max(
            self.url_btn.sizeHint().height(), self.summarize_btn.sizeHint().height()
        ) * 2
        self.url_edit.setMinimumHeight(
            two_btn_h + self.quiz_btn.sizeHint().height() + btn_layout.spacing()
        )

        url_layout = QtWidgets.QHBoxLayout()
        url_layout.addWidget(self.url_edit, 7)
        url_layout.addLayout(btn_layout, 1)
        layout.addLayout(url_layout)

        self.quiz_scroll.setWidgetResizable(True)
        self.quiz_layout.setContentsMargins(4, 4, 4, 4)
        self.quiz_layout.setSpacing(6)
        self.quiz_scroll.setWidget(self.quiz_container)
        self.quiz_scroll.setVisible(False)

        layout.addWidget(self.quiz_scroll, 4)
        layout.addStretch(1)

    # ---- public API -------------------------------------------------
    def clear_url(self) -> None:
        self.url_edit.clear()

    def set_quiz_busy(self, busy: bool) -> None:
        self.quiz_btn.setEnabled(not busy)
        self.quiz_progress.setVisible(busy)

    def populate_quiz(self, qa_pairs: list[tuple[str, str]]) -> None:
        clear_layout(self.quiz_layout)
        for question, answer in qa_pairs:
            self.quiz_layout.addWidget(QAItem(question, answer))
        if qa_pairs:
            self.quiz_layout.addStretch(1)
        self.quiz_scroll.setVisible(bool(qa_pairs))

    # ---- internal slots --------------------------------------------
    def _on_url_clicked(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            QtWidgets.QMessageBox.information(self, "error", "空です。")
            return
        self.urlSubmitted.emit(url)

    def _on_summarize_clicked(self) -> None:
        self.summarizeRequested.emit()

    def _on_quiz_clicked(self) -> None:
        self.quizRequested.emit()
