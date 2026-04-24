"""Dialog for creating a rich text narrative block."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class AddTextBlockDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, initial_html: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Add Narrative Text")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Enter narrative text. Standard formatting (bold, italics) is supported if pasted."))

        self._text_edit = QTextEdit()
        self._text_edit.setAcceptRichText(True)
        if initial_html:
            self._text_edit.setHtml(initial_html)
        else:
            self._text_edit.setPlaceholderText("Type your narrative here...")
            
        layout.addWidget(self._text_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_html(self) -> str:
        """Return the rich text as HTML."""
        return self._text_edit.toHtml()
    
    def get_plain_text(self) -> str:
        return self._text_edit.toPlainText()
