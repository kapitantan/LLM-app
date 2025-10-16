from __future__ import annotations

from PySide6 import QtCore

from summarizer_core import LLM_gen, make_quiz


class SummarizeWorker(QtCore.QRunnable):
    """Run text summarization in a background thread."""

    class Signals(QtCore.QObject):
        finished = QtCore.Signal(str, str)

    def __init__(self, text: str, max_sentences: int):
        super().__init__()
        self.text = text
        self.max_sentences = max_sentences
        self.signals = SummarizeWorker.Signals()

    @QtCore.Slot()
    def run(self) -> None:
        try:
            result = LLM_gen(contents="以下の文章を要約してください。" + self.text)
            self.signals.finished.emit("ok", result)
        except Exception as exc:  # noqa: BLE001
            self.signals.finished.emit("error", str(exc))


class QuizWorker(QtCore.QRunnable):
    """Generate quizzes from markdown without blocking the UI."""

    class Signals(QtCore.QObject):
        finished = QtCore.Signal(str, object)

    def __init__(self, markdown_text: str, num_questions: int):
        super().__init__()
        self.markdown_text = markdown_text
        self.num_questions = num_questions
        self.signals = QuizWorker.Signals()

    @QtCore.Slot()
    def run(self) -> None:
        try:
            qa_pairs = make_quiz(self.markdown_text, self.num_questions)
            self.signals.finished.emit("ok", qa_pairs)
        except Exception as exc:  # noqa: BLE001
            self.signals.finished.emit("error", exc)
