# app.py
import sys
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtWidgets, QtGui

from summarizer_core import load_gemini_api_key, LLM_gen, save_json, summarize_json, make_quiz

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


class QuizWorker(QtCore.QRunnable):
    """Background worker to generate quizzes without blocking the UI."""

    class Signals(QtCore.QObject):
        finished = QtCore.Signal(str, object)

    def __init__(self, markdown_text: str, num_questions: int):
        super().__init__()
        self.markdown_text = markdown_text
        self.num_questions = num_questions
        self.signals = QuizWorker.Signals()

    @QtCore.Slot()
    def run(self):
        try:
            qa_pairs = make_quiz(self.markdown_text, self.num_questions)
            self.signals.finished.emit("ok", qa_pairs)
        except Exception as exc:
            self.signals.finished.emit("error", exc)

class QAItem(QtWidgets.QWidget):
    """Q(ボタン)を押すとA(ラベル)が開閉する簡易アコーディオン"""
    def __init__(self, question: str, answer: str, parent=None):
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

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.addWidget(self.btn)
        lay.addWidget(self.ans)

    def _toggle(self, on: bool):
        self.ans.setVisible(on)
        self.btn.setArrowType(QtCore.Qt.DownArrow if on else QtCore.Qt.RightArrow)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Summarizer")
        self.resize(1000, 680)
        self.current_markdown_content: str = ""
        self._markdown_quiz_worker: Optional[QuizWorker] = None
        self._youtube_quiz_worker: Optional[QuizWorker] = None

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
    '''ページUI'''
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

        self.md_quiz_btn = QtWidgets.QPushButton("選択Markdownからクイズ生成 (10問)")
        self.md_quiz_btn.setEnabled(False)
        self.md_quiz_btn.clicked.connect(self.on_markdown_quiz_clicked)

        self.md_quiz_progress = QtWidgets.QProgressBar()
        self.md_quiz_progress.setRange(0, 0)
        self.md_quiz_progress.setVisible(False)

        self.md_quiz_scroll = QtWidgets.QScrollArea()
        self.md_quiz_scroll.setWidgetResizable(True)
        self.md_quiz_container = QtWidgets.QWidget()
        self.md_quiz_layout = QtWidgets.QVBoxLayout(self.md_quiz_container)
        self.md_quiz_layout.setContentsMargins(4, 4, 4, 4)
        self.md_quiz_layout.setSpacing(6)
        self.md_quiz_scroll.setWidget(self.md_quiz_container)
        self.md_quiz_scroll.setVisible(False)

        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("Summary フォルダ内ファイル"))
        left.addWidget(self.file_list, 1)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel("選択ファイル内容（プレビュー）"))
        right.addWidget(self.md_viewer, 2)
        right.addWidget(self.md_quiz_btn)
        right.addWidget(self.md_quiz_progress)
        right.addWidget(self.md_quiz_scroll, 3)

        body = QtWidgets.QHBoxLayout(parent)
        body.addLayout(left, 1)
        body.addLayout(right, 2)

    # ---------------------------
    # UI: youtubeページ
    # ---------------------------
    def _build_youtube_summarize_page(self, parent: QtWidgets.QWidget):
        layout = QtWidgets.QVBoxLayout(parent)

        # URL入力欄
        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText("YouTubeのURLを入力してください")

        # 右側ボタン群
        self.url_btn = QtWidgets.QPushButton("登録")
        self.url_btn.clicked.connect(self.on_url_clicked)

        self.summarize_btn = QtWidgets.QPushButton("要約開始")
        self.summarize_btn.clicked.connect(self.on_summarize_clicked)

        # ★追加：クイズ生成ボタン
        self.quiz_btn = QtWidgets.QPushButton("クイズ生成")
        self.quiz_btn.clicked.connect(self.on_quiz_clicked)
        self.quiz_btn.setEnabled(True)  # 要件次第で要約完了後に有効化する運用も可

        # 進捗バーを追加
        self.quiz_progress = QtWidgets.QProgressBar()
        self.quiz_progress.setRange(0, 0)
        self.quiz_progress.setVisible(False)

        # 右カラム(縦)に3ボタン
        btn_layout = QtWidgets.QVBoxLayout()
        btn_layout.addWidget(self.url_btn, 1)
        btn_layout.addWidget(self.summarize_btn, 1)
        btn_layout.addWidget(self.quiz_btn, 1)
        btn_layout.addWidget(self.quiz_progress, 1)  # 進捗バーを追加

        # 伸縮ポリシー（既存と同様）
        spx = QtWidgets.QSizePolicy.Expanding
        spy = QtWidgets.QSizePolicy.Expanding
        self.url_edit.setSizePolicy(spx, spy)
        self.url_btn.setSizePolicy(spx, spy)
        self.summarize_btn.setSizePolicy(spx, spy)
        self.quiz_btn.setSizePolicy(spx, spy)

        two_btn_h = max(self.url_btn.sizeHint().height(),
                        self.summarize_btn.sizeHint().height()) * 2
        # ボタンが1つ増えたので3個分を見越して少しだけ余裕を足す
        self.url_edit.setMinimumHeight(two_btn_h + self.quiz_btn.sizeHint().height() + btn_layout.spacing())

        # 左(入力) + 右(ボタン) を横並び
        url_layout = QtWidgets.QHBoxLayout()
        url_layout.addWidget(self.url_edit, 7)
        url_layout.addLayout(btn_layout, 1)

        layout.addLayout(url_layout)

        # ★追加：クイズ表示領域（スクロール可、初期は非表示）
        self.quiz_scroll = QtWidgets.QScrollArea()
        self.quiz_scroll.setWidgetResizable(True)
        self.quiz_container = QtWidgets.QWidget()
        self.quiz_layout = QtWidgets.QVBoxLayout(self.quiz_container)
        self.quiz_layout.setContentsMargins(4, 4, 4, 4)
        self.quiz_layout.setSpacing(6)
        self.quiz_scroll.setWidget(self.quiz_container)
        self.quiz_scroll.setVisible(False)  # 生成されるまで隠す

        layout.addWidget(self.quiz_scroll, 4)
        layout.addStretch(1)
 
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
            self.current_markdown_content = content
            self.md_quiz_btn.setEnabled(True)
            self.populate_markdown_quiz([])
            self.statusBar().showMessage(f"読み込み: {file_path.name}")
        except Exception as e:
            self.md_viewer.setPlainText(f"[ERROR] {e}")
            self.statusBar().showMessage("読み込みに失敗しました")
            self.current_markdown_content = ""
            self.md_quiz_btn.setEnabled(False)
            self.populate_markdown_quiz([])
    # ---------------------------
    # 要約ページ：要約ボタン
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
    # ---------------------------
    # 要約ページ：
    # ---------------------------
    @QtCore.Slot(str, str)
    def on_finished(self, status: str, payload: str):
        self.progress.setVisible(False)
        self.btn.setEnabled(True)
        if status == "ok":
            self.output_edit.setPlainText(payload)
        else:
            self.output_edit.setPlainText(f"[ERROR] {payload}")
    
    # ---------------------------
    # youtubeページ：URL登録ボタン
    # ---------------------------
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
    
    # ---------------------------
    # youtubeページ：jsonファイルを参照する要約ボタン
    # ---------------------------
    @QtCore.Slot()
    def on_summarize_clicked(self):
        summarize_json()
    
    # ---------------------------
    # youtubeページ：クイズ生成ボタン
    # ---------------------------
    @QtCore.Slot()
    def on_quiz_clicked(self):
        """
        クイズ生成ボタン押下時：
        - 10問のQ/Aを作り、リンク入力欄の下に並べる
        - クリックで回答が開閉
        """
        # プログレスバーを表示して処理中をユーザーに示す
        self.quiz_progress.setVisible(True)
        self.quiz_btn.setEnabled(False)
        
        combined_summary = self._collect_all_summaries()
        if not combined_summary.strip():
            QtWidgets.QMessageBox.information(
                self, "情報", "要約ファイルが見つからないためクイズを生成できません。"
            )
            self.quiz_progress.setVisible(False)
            self.quiz_btn.setEnabled(True)
            self.statusBar().showMessage("生成可能な要約が見つかりませんでした")
            return

        worker = QuizWorker(combined_summary, 10)
        worker.signals.finished.connect(self._on_youtube_quiz_finished)
        self._youtube_quiz_worker = worker
        self.pool.start(worker)
    # ---------------------------
    # youtubeページ：表示を初期化してQ/Aアイテムを縦に並べる
    # ---------------------------
    def populate_quiz(self, qa_pairs: list[tuple[str, str]]):
        self._clear_layout(self.quiz_layout)
        for q, a in qa_pairs:
            self.quiz_layout.addWidget(QAItem(q, a))
        if qa_pairs:
            self.quiz_layout.addStretch(1)
        self.quiz_scroll.setVisible(bool(qa_pairs))

    def populate_markdown_quiz(self, qa_pairs: list[tuple[str, str]]):
        self._clear_layout(self.md_quiz_layout)
        for q, a in qa_pairs:
            self.md_quiz_layout.addWidget(QAItem(q, a))
        if qa_pairs:
            self.md_quiz_layout.addStretch(1)
        self.md_quiz_scroll.setVisible(bool(qa_pairs))

    def _clear_layout(self, layout: QtWidgets.QLayout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
    # ---------------------------
    # youtubeページ：デモ用のダミーQ/A生成
    # ---------------------------
    def _demo_make_dummy_qa(self, n: int) -> list[tuple[str, str]]:
        qa = []
        for i in range(1, n + 1):
            q = f"Q{i}. 動画の主要トピック{i}は？（クリックで回答）"
            a = f"A{i}. ここに回答{i}が入ります。実装では要約から抽出/生成してください。"
            qa.append((q, a))
        return qa
    # ---------------------------
    # youtubeページ：Q/A生成
    # ---------------------------
    @QtCore.Slot()
    def on_markdown_quiz_clicked(self):
        if not self.current_markdown_content.strip():
            QtWidgets.QMessageBox.information(self, "情報", "Markdownを選択してください。")
            return

        self.md_quiz_btn.setEnabled(False)
        self.md_quiz_progress.setVisible(True)

        worker = QuizWorker(self.current_markdown_content, 10)
        worker.signals.finished.connect(self._on_markdown_quiz_finished)
        self._markdown_quiz_worker = worker
        self.pool.start(worker)

    def _on_youtube_quiz_finished(self, status: str, payload: object):
        self.quiz_progress.setVisible(False)
        self.quiz_btn.setEnabled(True)
        self._youtube_quiz_worker = None

        if status == "ok":
            qa_raw = payload if isinstance(payload, list) else []
            formatted = self._format_quiz_pairs(qa_raw, 10)
            if formatted:
                self.populate_quiz(formatted)
                self.statusBar().showMessage("クイズを生成しました（10問）")
            else:
                self.populate_quiz([])
                self.statusBar().showMessage("クイズを生成できませんでした")
                QtWidgets.QMessageBox.warning(
                    self, "エラー", "クイズを生成できませんでした。要約内容を確認してください。"
                )
        else:
            self.populate_quiz([])
            self.statusBar().showMessage("クイズ生成に失敗しました")
            QtWidgets.QMessageBox.warning(
                self, "エラー", f"クイズ生成に失敗しました: {payload}"
            )

    def _on_markdown_quiz_finished(self, status: str, payload: object):
        self.md_quiz_progress.setVisible(False)
        self.md_quiz_btn.setEnabled(True)
        self._markdown_quiz_worker = None

        if status == "ok":
            qa_raw = payload if isinstance(payload, list) else []
            formatted = self._format_quiz_pairs(qa_raw, 10)
            if formatted:
                self.populate_markdown_quiz(formatted)
                self.statusBar().showMessage("選択したMarkdownからクイズを生成しました（10問）")
            else:
                self.populate_markdown_quiz([])
                self.statusBar().showMessage("クイズを生成できませんでした")
                QtWidgets.QMessageBox.warning(
                    self, "エラー", "クイズを生成できませんでした。要約内容を確認してください。"
                )
        else:
            self.populate_markdown_quiz([])
            self.statusBar().showMessage("クイズ生成に失敗しました")
            QtWidgets.QMessageBox.warning(
                self, "エラー", f"クイズ生成に失敗しました: {payload}"
            )

    def _format_quiz_pairs(self, qa_raw: list[tuple[str, str]], max_items: int) -> list[tuple[str, str]]:
        formatted: list[tuple[str, str]] = []
        for idx, item in enumerate(qa_raw, start=1):
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            question, answer = item
            q = f"Q{idx}. {question}（クリックで回答）"
            a = f"A{idx}. {answer}"
            formatted.append((q, a))
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

def main():
    load_gemini_api_key()
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
