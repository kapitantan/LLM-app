# app.py
import sys
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from summarizer_core import load_gemini_api_key, LLM_gen, save_json, summarize_json

SUMMARY_DIR = Path(__file__).parent / "summary"
SUMMARIZE_STR = "要約画面"
MARKDOWN_PEWVIEW_STR = "Markdownプレビュー"
YOUTUBE_SUMMARIZE_STR = "youtube要約"


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

        # ==== ページ3：youtubeリンク読み込み要約 ====
        self.page_youtybe_summarize = QtWidgets.QWidget()
        self._build_youtube_summarize_page(self.page_youtybe_summarize)
        self.stack.addWidget(self.page_youtybe_summarize)

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
        self.md_viewer.setPlaceholderText(
            "summary フォルダの Markdown をプレビュー表示"
        )

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
    # UI: youtube要約
    # ---------------------------
    def _build_youtube_summarize_page(self, parent: QtWidgets.QWidget):
        layout = QtWidgets.QVBoxLayout(parent)

        # URL入力欄
        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText("YouTubeのURLを入力してください")

        # 読み込みボタン
        self.url_btn = QtWidgets.QPushButton("登録")
        self.url_btn.clicked.connect(self.on_url_clicked)
        # 要約ボタン
        self.summarize_btn = QtWidgets.QPushButton("要約開始")
        self.summarize_btn.clicked.connect(self.on_summarize_clicked)

        # 横並び
        url_layout = QtWidgets.QHBoxLayout()
        url_layout.addWidget(self.url_edit, 7)
        url_layout.addWidget(self.url_btn, 1)
        url_layout.addWidget(self.summarize_btn, 1)

        layout.addLayout(url_layout)
        layout.addStretch(1)  # 下の余白

    # ---------------------------
    # メニュー
    # ---------------------------
    def _build_menu(self):
        menubar = self.menuBar()

        menu_view = menubar.addMenu("表示(&V)")

        act_summarize = QtGui.QAction(SUMMARIZE_STR + "(&S)", self)
        act_summarize.setShortcut("Ctrl+1")
        act_summarize.triggered.connect(lambda: self.switch_page(0))
        menu_view.addAction(act_summarize)

        act_markdown = QtGui.QAction(MARKDOWN_PEWVIEW_STR + "(&M)", self)
        act_markdown.setShortcut("Ctrl+2")
        act_markdown.triggered.connect(lambda: self.switch_page(1))
        menu_view.addAction(act_markdown)

        act_youtube_summarize = QtGui.QAction(YOUTUBE_SUMMARIZE_STR + "(&M)", self)
        act_youtube_summarize.setShortcut("Ctrl+3")
        act_youtube_summarize.triggered.connect(lambda: self.switch_page(2))
        menu_view.addAction(act_youtube_summarize)

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
            "Python Summarizer\n\nCtrl+1: "
            + SUMMARIZE_STR
            + " / Ctrl+2: "
            + MARKDOWN_PEWVIEW_STR
            + " \nF5: ファイル一覧再読込",
        )

    # ---------------------------
    # 画面切替
    # ---------------------------
    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        match index:
            case 0:
                name = SUMMARIZE_STR
            case 1:
                name = MARKDOWN_PEWVIEW_STR
            case 2:
                name = YOUTUBE_SUMMARIZE_STR
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

    '''youtubeのURL登録'''
    @QtCore.Slot()
    def on_url_clicked(self):
        url = self.url_edit.text().strip()
        if not url:
            QtWidgets.QMessageBox.information(self, "error", "空です。")
            return

        print(f"{url=}")
        result = save_json(url)

        if result:  # 保存成功したら入力欄をクリア
            self.url_edit.clear()
        else:
            QtWidgets.QMessageBox.warning(self, "error", "Invalid URL")
    '''jsonファイルを参照して要約'''
    @QtCore.Slot()
    def on_summarize_clicked(self):
        summarize_json()

def main():
    load_gemini_api_key()
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
