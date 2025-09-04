# app.py
import sys
import os
from pathlib import Path
from PySide6 import QtCore, QtWidgets
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


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Summarizer")
        self.resize(900, 600)

        # --- 要約UI ---
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

        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(QtWidgets.QLabel("原文"))
        left_layout.addWidget(self.input_edit, 2)
        left_layout.addLayout(top)
        left_layout.addWidget(QtWidgets.QLabel("要約"))
        left_layout.addWidget(self.output_edit, 3)

        # --- summaryフォルダ内Markdown表示UI ---
        self.file_list = QtWidgets.QListWidget()
        self.file_list.itemClicked.connect(self.load_markdown)

        self.md_viewer = QtWidgets.QTextBrowser()  # ← QTextBrowser に変更
        self.md_viewer.setOpenExternalLinks(True)  # リンクは外部ブラウザで開く
        self.md_viewer.setPlaceholderText("summary フォルダの Markdown ファイルをプレビュー表示")

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(QtWidgets.QLabel("Summary フォルダ内ファイル"))
        right_layout.addWidget(self.file_list, 1)
        right_layout.addWidget(QtWidgets.QLabel("選択ファイル内容"))
        right_layout.addWidget(self.md_viewer, 3)


        # --- 全体レイアウト ---
        layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(left_layout, 2)
        layout.addLayout(right_layout, 1)

        # スレッドプール
        self.pool = QtCore.QThreadPool.globalInstance()

        # イベント
        self.btn.clicked.connect(self.on_click)

        # ファイル一覧読み込み
        self.load_file_list()

    def load_file_list(self):
        """summaryフォルダ内のmdファイルを一覧に表示"""
        self.file_list.clear()
        if SUMMARY_DIR.exists():
            for f in sorted(SUMMARY_DIR.glob("*.md")):
                self.file_list.addItem(f.name)

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def load_markdown(self, item):
        """選択されたMarkdownファイルをプレビュー表示"""
        file_path = SUMMARY_DIR / item.text()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.md_viewer.setMarkdown(content)  # ← Markdownとしてレンダリング
        except Exception as e:
            self.md_viewer.setPlainText(f"[ERROR] {e}")


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
