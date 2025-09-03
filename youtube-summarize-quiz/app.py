# app.py
import sys
from PySide6 import QtCore, QtWidgets
from summarizer_core import summarize

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
            result = summarize(self.text, self.max_sentences)
            self.signals.finished.emit("ok", result)
        except Exception as e:
            self.signals.finished.emit("error", str(e))

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Summarizer")
        self.resize(720, 520)

        # ウィジェット
        self.input_edit = QtWidgets.QPlainTextEdit()
        self.input_edit.setPlaceholderText("原文をここに貼り付け...")

        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(1, 20)
        self.spin.setValue(3)
        self.spin.setPrefix("最大文数: ")

        self.btn = QtWidgets.QPushButton("要約")
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)  # インジケータ（ぐるぐる）
        self.progress.setVisible(False)

        self.output_edit = QtWidgets.QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("ここに要約が表示されます")

        # レイアウト
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

        # スレッドプール
        self.pool = QtCore.QThreadPool.globalInstance()

        # イベント
        self.btn.clicked.connect(self.on_click)

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
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

