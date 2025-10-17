from __future__ import annotations

from typing import Iterable

from PySide6 import QtCore, QtWidgets

from ui.widgets import QAItem, clear_layout


class MarkdownPreviewPage(QtWidgets.QWidget):
    fileSelected = QtCore.Signal(str)
    quizRequested = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.file_list = QtWidgets.QListWidget()
        self.md_viewer = QtWidgets.QTextBrowser()
        self.md_quiz_btn = QtWidgets.QPushButton("選択Markdownからクイズ生成 (10問)")
        self.md_quiz_progress = QtWidgets.QProgressBar()
        self.md_quiz_scroll = QtWidgets.QScrollArea()
        self.md_quiz_container = QtWidgets.QWidget()
        self.md_quiz_layout = QtWidgets.QVBoxLayout(self.md_quiz_container)
        self.current_markdown_content = ""
        self._build_ui()

    def _build_ui(self) -> None:
        self.file_list.itemClicked.connect(self._on_file_clicked)

        self.md_viewer.setOpenExternalLinks(True)
        self.md_viewer.setPlaceholderText("summary フォルダの Markdown をプレビュー表示")

        self.md_quiz_btn.setEnabled(False)
        self.md_quiz_btn.clicked.connect(self._on_quiz_clicked)

        self.md_quiz_progress.setRange(0, 0)
        self.md_quiz_progress.setVisible(False)

        self.md_quiz_scroll.setWidgetResizable(True)
        self.md_quiz_layout.setContentsMargins(4, 4, 4, 4)
        self.md_quiz_layout.setSpacing(6)
        self.md_quiz_scroll.setWidget(self.md_quiz_container)
        self.md_quiz_scroll.setVisible(False)

        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("Summary フォルダ内ファイル"))
        left.addWidget(self.file_list, 1)

        preview_panel = QtWidgets.QWidget()
        preview_layout = QtWidgets.QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(6)
        preview_layout.addWidget(QtWidgets.QLabel("選択ファイル内容（プレビュー）"))
        preview_layout.addWidget(self.md_viewer, 1)

        quiz_panel = QtWidgets.QWidget()
        quiz_layout = QtWidgets.QVBoxLayout(quiz_panel)
        quiz_layout.setContentsMargins(0, 0, 0, 0)
        quiz_layout.setSpacing(6)
        quiz_layout.addWidget(self.md_quiz_btn)
        quiz_layout.addWidget(self.md_quiz_progress)
        quiz_layout.addWidget(self.md_quiz_scroll, 1)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        splitter.setHandleWidth(6)
        splitter.addWidget(preview_panel)
        splitter.addWidget(quiz_panel)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, True)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([400, 200])

        right = QtWidgets.QVBoxLayout()
        right.addWidget(splitter)

        body = QtWidgets.QHBoxLayout(self)
        body.addLayout(left, 1)
        body.addLayout(right, 2)

    # ---- public API -------------------------------------------------
    def set_files(self, filenames: Iterable[str]) -> None:
        self.file_list.clear()
        for name in filenames:
            self.file_list.addItem(name)

    def set_markdown_content(self, content: str) -> None:
        self.current_markdown_content = content
        if content:
            self.md_viewer.setMarkdown(content)
            self.md_quiz_btn.setEnabled(True)
        else:
            self.md_viewer.clear()
            self.md_quiz_btn.setEnabled(False)
        self.populate_quiz([])

    def set_busy(self, busy: bool) -> None:
        self.md_quiz_btn.setEnabled(not busy and bool(self.current_markdown_content.strip()))
        self.md_quiz_progress.setVisible(busy)

    def populate_quiz(self, qa_pairs: list[tuple[str, str]]) -> None:
        clear_layout(self.md_quiz_layout)
        for question, answer in qa_pairs:
            self.md_quiz_layout.addWidget(QAItem(question, answer))
        if qa_pairs:
            self.md_quiz_layout.addStretch(1)
        self.md_quiz_scroll.setVisible(bool(qa_pairs))

    # ---- internal slots --------------------------------------------
    def _on_file_clicked(self, item: QtWidgets.QListWidgetItem) -> None:
        self.fileSelected.emit(item.text())

    def _on_quiz_clicked(self) -> None:
        if not self.current_markdown_content.strip():
            QtWidgets.QMessageBox.information(self, "情報", "Markdownを選択してください。")
            return

        self.set_busy(True)
        self.quizRequested.emit(self.current_markdown_content)
