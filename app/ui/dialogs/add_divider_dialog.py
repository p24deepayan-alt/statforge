"""Dialog for inserting a visual divider into the report."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class AddDividerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add Divider")
        self.setMinimumSize(300, 150)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select Divider Style:"))

        self._style_combo = QComboBox()
        self._style_combo.addItems([
            "Solid Line",
            "Dashed Line",
            "Page Break"
        ])
        layout.addWidget(self._style_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_style(self) -> str:
        text = self._style_combo.currentText()
        if text == "Page Break":
            return "pagebreak"
        elif text == "Dashed Line":
            return "dashed"
        return "solid"
