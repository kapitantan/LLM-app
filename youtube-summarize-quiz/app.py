# app.py
import sys
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from summarizer_core import load_gemini_api_key, LLM_gen

SUMMARY_DIR = Path(__file__).parent / "summary"


class SummarizeWorker(QtCore.QRunnable):
    """
    別スレッドで要約を実行するワーカー。
    結果はシグナルでUIスレッドに戻す。
    """
    class Signals(QtCore.QObject):
        finished = QtCore.Signal(str, str)  # (status, payload_or_error)

    def __init__(self, text: str, max_sentences: int):
        super().__init__()
        self.text = text
        self.max_sentences = max_sentences
        self.signals = SummarizeWorker.Signals()

    @QtCore.Slot()
    def run(self):
        try:
            result = LLM_gen(contents="以下の文章を要約してください。" + self.text)
            self.signals.finished.emit("ok", result)
        except Exception as e:
            self.signals.finished.emit("error", str(e))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Summarizer")
        self.resize(1000, 680)

        # ---- ページコンテナ（画面切替用） ----
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        # ==== ページ1：要約 ====
        self.page_summarize = QtWidgets.QWidget()
        self._build_summarize_page(self.page_summarize)
        self.stack.addWidget(self.page_summarize)

        # ==== ページ2：Markdownプレビュー ====
        self.page_markdown = QtWidgets.QWidget()
        self._build_markdown_page(self.page_markdown)
        self.stack.addWidget(self.page_markdown)

        # ---- スレッドプール ----
        self.pool = QtCore.QThreadPool.globalInstance()

        # ---- メニューバー ----
        self._build_menu()

        # ---- 初期化 ----
        self.load_file_list()
        self.statusBar().showMessage("準備完了")

    # ---------------------------
    # UI: 要約ページ
    # ---------------------------
    def _build_summarize_page(self, parent: QtWidgets.QWidget):
        self.input_edit = QtWidgets.QPlainTextEdit()
        self.input_edit.setPlaceholderText("原文をここに貼り付け...")

        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(1, 20)
        self.spin.setValue(3)
        self.spin.setPrefix("最大文数: ")

        self.btn = QtWidgets.QPushButton("要約")
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)

        self.output_edit = QtWidgets.QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("ここに要約が表示されます")

        top = QtWidgets.QHBoxLayout()
        top.addWidget(self.spin)
        top.addStretch(1)
        top.addWidget(self.btn)
        top.addWidget(self.progress)

        layout = QtWidgets.QVBoxLayout(parent)
        layout.addWidget(QtWidgets.QLabel("原文"))
        layout.addWidget(self.input_edit, 2)
        layout.addLayout(top)
        layout.addWidget(QtWidgets.QLabel("要約"))
        layout.addWidget(self.output_edit, 3)

        # イベント
        self.btn.clicked.connect(self.on_click)

    # ---------------------------
    # UI: Markdownプレビューページ
    # ---------------------------
    def _build_markdown_page(self, parent: QtWidgets.QWidget):
        self.file_list = QtWidgets.QListWidget()
        self.file_list.itemClicked.connect(self.load_markdown)

        self.md_viewer = QtWidgets.QTextBrowser()  # Markdown簡易レンダリング対応
        self.md_viewer.setOpenExternalLinks(True)
        self.md_viewer.setPlaceholderText("summary フォルダの Markdown をプレビュー表示")

        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("Summary フォルダ内ファイル"))
        left.addWidget(self.file_list, 1)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel("選択ファイル内容（プレビュー）"))
        right.addWidget(self.md_viewer, 1)

        body = QtWidgets.QHBoxLayout(parent)
        body.addLayout(left, 1)
        body.addLayout(right, 2)

    # ---------------------------
    # メニュー
    # ---------------------------
    def _build_menu(self):
        menubar = self.menuBar()

        menu_view = menubar.addMenu("表示(&V)")

        act_summarize = QtGui.QAction("要約画面(&S)", self)
        act_summarize.setShortcut("Ctrl+1")
        act_summarize.triggered.connect(lambda: self.switch_page(0))
        menu_view.addAction(act_summarize)

        act_markdown = QtGui.QAction("Markdownプレビュー(&M)", self)
        act_markdown.setShortcut("Ctrl+2")
        act_markdown.triggered.connect(lambda: self.switch_page(1))
        menu_view.addAction(act_markdown)

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
    def _show_about(self):
        QtWidgets.QMessageBox.information(
            self,
            "About",
            "Python Summarizer\n\nCtrl+1: 要約画面 / Ctrl+2: Markdownプレビュー\nF5: ファイル一覧再読込",
        )

    # ---------------------------
    # 画面切替
    # ---------------------------
    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        name = "要約画面" if index == 0 else "Markdownプレビュー"
        self.statusBar().showMessage(f"{name} に切り替えました")

    # ---------------------------
    # Markdown一覧・表示
    # ---------------------------
    def load_file_list(self):
        """summaryフォルダ内のmdファイルを一覧に表示"""
        self.file_list.clear()
        if SUMMARY_DIR.exists():
            for f in sorted(SUMMARY_DIR.glob("*.md")):
                self.file_list.addItem(f.name)
            self.statusBar().showMessage("Markdownファイル一覧を更新しました")
        else:
            self.statusBar().showMessage("summary フォルダが見つかりません")

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def load_markdown(self, item):
        """選択されたMarkdownファイルをプレビュー表示"""
        file_path = SUMMARY_DIR / item.text()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # QTextBrowserは Markdown を簡易レンダリング可能
            self.md_viewer.setMarkdown(content)
            self.statusBar().showMessage(f"読み込み: {file_path.name}")
        except Exception as e:
            self.md_viewer.setPlainText(f"[ERROR] {e}")
            self.statusBar().showMessage("読み込みに失敗しました")

    # ---------------------------
    # 要約ジョブ
    # ---------------------------
    @QtCore.Slot()
    def on_click(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            QtWidgets.QMessageBox.information(self, "情報", "原文が空です。")
            return

        self.btn.setEnabled(False)
        self.progress.setVisible(True)
        self.output_edit.clear()

        worker = SummarizeWorker(text, self.spin.value())
        worker.signals.finished.connect(self.on_finished)
        self.pool.start(worker)

    @QtCore.Slot(str, str)
    def on_finished(self, status: str, payload: str):
        self.progress.setVisible(False)
        self.btn.setEnabled(True)
        if status == "ok":
            self.output_edit.setPlainText(payload)
        else:
            self.output_edit.setPlainText(f"[ERROR] {payload}")


def main():
    load_gemini_api_key()
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
