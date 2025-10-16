from __future__ import annotations

import sys
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from ui.constants import (
    MARKDOWN_PREVIEW_STR,
    SUMMARY_DIR,
    SUMMARIZE_STR,
    YOUTUBE_SUMMARIZE_STR,
)
from ui.pages.markdown import MarkdownPreviewPage
from ui.pages.summarize import SummarizePage
from ui.pages.youtube import YouTubeSummarizePage
from ui.workers import QuizWorker, SummarizeWorker
from summarizer_core import load_gemini_api_key, save_json, summarize_json


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Python Summarizer")
        self.resize(1000, 680)

        self._summarize_worker: Optional[SummarizeWorker] = None
        self._markdown_quiz_worker: Optional[QuizWorker] = None
        self._youtube_quiz_worker: Optional[QuizWorker] = None

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.summarize_page = SummarizePage()
        self.markdown_page = MarkdownPreviewPage()
        self.youtube_page = YouTubeSummarizePage()

        self.stack.addWidget(self.markdown_page)
        self.stack.addWidget(self.youtube_page)
        self.stack.addWidget(self.summarize_page)

        self.summarize_page.summarizeRequested.connect(self._on_summarize_requested)
        self.markdown_page.fileSelected.connect(self._on_markdown_file_selected)
        self.markdown_page.quizRequested.connect(self._on_markdown_quiz_requested)
        self.youtube_page.urlSubmitted.connect(self._on_url_submitted)
        self.youtube_page.summarizeRequested.connect(self._on_youtube_summarize_requested)
        self.youtube_page.quizRequested.connect(self._on_youtube_quiz_requested)

        self.pool = QtCore.QThreadPool.globalInstance()

        self._build_menu()

        self.load_file_list()
        self.statusBar().showMessage("準備完了")

    # ---------------------------
    # メニュー
    # ---------------------------
    def _build_menu(self) -> None:
        menubar = self.menuBar()

        menu_view = menubar.addMenu("表示(&V)")

        act_summarize = QtGui.QAction(MARKDOWN_PREVIEW_STR + "(&S)", self)
        act_summarize.setShortcut("Ctrl+1")
        act_summarize.triggered.connect(lambda: self.switch_page(0))
        menu_view.addAction(act_summarize)

        act_markdown = QtGui.QAction(YOUTUBE_SUMMARIZE_STR + "(&M)", self)
        act_markdown.setShortcut("Ctrl+2")
        act_markdown.triggered.connect(lambda: self.switch_page(1))
        menu_view.addAction(act_markdown)

        act_youtube = QtGui.QAction(SUMMARIZE_STR + "(&Y)", self)
        act_youtube.setShortcut("Ctrl+3")
        act_youtube.triggered.connect(lambda: self.switch_page(2))
        menu_view.addAction(act_youtube)

        menu_view.addSeparator()

        act_reload = QtGui.QAction("ファイル一覧を再読込(&R)", self)
        act_reload.setShortcut("F5")
        act_reload.triggered.connect(self.load_file_list)
        menu_view.addAction(act_reload)

        menu_help = menubar.addMenu("ヘルプ(&H)")
        act_about = QtGui.QAction("このアプリについて", self)
        act_about.triggered.connect(self._show_about)
        menu_help.addAction(act_about)

    @QtCore.Slot()
    def _show_about(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "About",
            "Python Summarizer\n\nCtrl+1: "
            + SUMMARIZE_STR
            + " / Ctrl+2: "
            + MARKDOWN_PREVIEW_STR
            + " \nF5: ファイル一覧再読込",
        )

    # ---------------------------
    # 画面切替
    # ---------------------------
    def switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if index == 0:
            name = SUMMARIZE_STR
        elif index == 1:
            name = MARKDOWN_PREVIEW_STR
        else:
            name = YOUTUBE_SUMMARIZE_STR
        self.statusBar().showMessage(f"{name} に切り替えました")

    # ---------------------------
    # Markdown一覧・表示
    # ---------------------------
    def load_file_list(self) -> None:
        self.markdown_page.set_files([])
        if SUMMARY_DIR.exists():
            files = sorted(f.name for f in SUMMARY_DIR.glob("*.md"))
            self.markdown_page.set_files(files)
            self.statusBar().showMessage("Markdownファイル一覧を更新しました")
        else:
            self.statusBar().showMessage("summary フォルダが見つかりません")

    @QtCore.Slot(str)
    def _on_markdown_file_selected(self, filename: str) -> None:
        file_path = SUMMARY_DIR / filename
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            self.markdown_page.set_markdown_content("")
            self.markdown_page.populate_quiz([])
            self.statusBar().showMessage("読み込みに失敗しました")
            QtWidgets.QMessageBox.warning(self, "エラー", f"読み込みに失敗しました: {exc}")
            return

        self.markdown_page.set_markdown_content(content)
        self.statusBar().showMessage(f"読み込み: {file_path.name}")

    # ---------------------------
    # 要約ページ
    # ---------------------------
    @QtCore.Slot(str, int)
    def _on_summarize_requested(self, text: str, max_sentences: int) -> None:
        worker = SummarizeWorker(text, max_sentences)
        worker.signals.finished.connect(self._on_summarize_finished)
        self._summarize_worker = worker
        self.pool.start(worker)

    def _on_summarize_finished(self, status: str, payload: str) -> None:
        self._summarize_worker = None
        self.summarize_page.set_busy(False)
        if status == "ok":
            self.summarize_page.show_result(payload)
        else:
            self.summarize_page.show_error(payload)

    # ---------------------------
    # Markdownページ：クイズ
    # ---------------------------
    @QtCore.Slot(str)
    def _on_markdown_quiz_requested(self, content: str) -> None:
        worker = QuizWorker(content, 10)
        worker.signals.finished.connect(self._on_markdown_quiz_finished)
        self._markdown_quiz_worker = worker
        self.pool.start(worker)

    def _on_markdown_quiz_finished(self, status: str, payload: object) -> None:
        self._markdown_quiz_worker = None
        self.markdown_page.set_busy(False)

        if status == "ok":
            qa_raw = payload if isinstance(payload, list) else []
            formatted = self._format_quiz_pairs(qa_raw, 10)
            if formatted:
                self.markdown_page.populate_quiz(formatted)
                self.statusBar().showMessage("選択したMarkdownからクイズを生成しました（10問）")
            else:
                self.markdown_page.populate_quiz([])
                self.statusBar().showMessage("クイズを生成できませんでした")
                QtWidgets.QMessageBox.warning(
                    self, "エラー", "クイズを生成できませんでした。要約内容を確認してください。"
                )
        else:
            self.markdown_page.populate_quiz([])
            self.statusBar().showMessage("クイズ生成に失敗しました")
            QtWidgets.QMessageBox.warning(
                self, "エラー", f"クイズ生成に失敗しました: {payload}"
            )

    # ---------------------------
    # YouTubeページ
    # ---------------------------
    @QtCore.Slot(str)
    def _on_url_submitted(self, url: str) -> None:
        print(f"{url=}")
        result = save_json(url)
        if result:
            self.youtube_page.clear_url()
            self.statusBar().showMessage("URLを登録しました")
        else:
            QtWidgets.QMessageBox.warning(self, "error", "Invalid URL")
            self.statusBar().showMessage("URLの登録に失敗しました")

    @QtCore.Slot()
    def _on_youtube_summarize_requested(self) -> None:
        summarize_json()

    @QtCore.Slot()
    def _on_youtube_quiz_requested(self) -> None:
        combined_summary = self._collect_all_summaries()
        if not combined_summary.strip():
            QtWidgets.QMessageBox.information(
                self, "情報", "要約ファイルが見つからないためクイズを生成できません。"
            )
            self.youtube_page.set_quiz_busy(False)
            self.statusBar().showMessage("生成可能な要約が見つかりませんでした")
            return

        self.youtube_page.set_quiz_busy(True)
        worker = QuizWorker(combined_summary, 10)
        worker.signals.finished.connect(self._on_youtube_quiz_finished)
        self._youtube_quiz_worker = worker
        self.pool.start(worker)

    def _on_youtube_quiz_finished(self, status: str, payload: object) -> None:
        self._youtube_quiz_worker = None
        self.youtube_page.set_quiz_busy(False)

        if status == "ok":
            qa_raw = payload if isinstance(payload, list) else []
            formatted = self._format_quiz_pairs(qa_raw, 10)
            if formatted:
                self.youtube_page.populate_quiz(formatted)
                self.statusBar().showMessage("クイズを生成しました（10問）")
            else:
                self.youtube_page.populate_quiz([])
                self.statusBar().showMessage("クイズを生成できませんでした")
                QtWidgets.QMessageBox.warning(
                    self, "エラー", "クイズを生成できませんでした。要約内容を確認してください。"
                )
        else:
            self.youtube_page.populate_quiz([])
            self.statusBar().showMessage("クイズ生成に失敗しました")
            QtWidgets.QMessageBox.warning(
                self, "エラー", f"クイズ生成に失敗しました: {payload}"
            )

    # ---------------------------
    # 共通ユーティリティ
    # ---------------------------
    def _format_quiz_pairs(
        self, qa_raw: list[tuple[str, str]], max_items: int
    ) -> list[tuple[str, str]]:
        formatted: list[tuple[str, str]] = []
        for idx, item in enumerate(qa_raw, start=1):
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            question, answer = item
            question_text = f"Q{idx}. {question}（クリックで回答）"
            answer_text = f"A{idx}. {answer}"
            formatted.append((question_text, answer_text))
            if idx >= max_items:
                break
        return formatted

    def _collect_all_summaries(self) -> str:
        collected: list[str] = []
        for summary_file in sorted(SUMMARY_DIR.glob("*.md")):
            try:
                collected.append(summary_file.read_text(encoding="utf-8"))
            except OSError:
                continue
        return "\n\n".join(collected)


def main() -> None:
    load_gemini_api_key()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
