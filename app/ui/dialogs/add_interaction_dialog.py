"""Dialog for adding interaction variables."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class AddInteractionDialog(QDialog):
    def __init__(self, columns: list[str], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add Interaction Variable")
        self.setMinimumSize(300, 150)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select Feature 1:"))
        self._feat1 = QComboBox()
        self._feat1.addItems(columns)
        layout.addWidget(self._feat1)

        layout.addWidget(QLabel("Select Feature 2:"))
        self._feat2 = QComboBox()
        self._feat2.addItems(columns)
        layout.addWidget(self._feat2)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_features(self) -> tuple[str, str]:
        return self._feat1.currentText(), self._feat2.currentText()
