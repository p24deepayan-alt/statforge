"""New Session dialog — name the session and pick a dataset file."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.util import strings


class NewSessionDialog(QDialog):
    """Modal dialog for creating a new session."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(strings.DLG_NEW_SESSION_TITLE)
        self.setMinimumWidth(460)
        self.setModal(True)
        self._file_path: Path | None = None

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel(strings.DLG_NEW_SESSION_TITLE)
        title.setProperty("class", "dialog_title")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #191c1c;")
        layout.addWidget(title)

        # Session name
        name_label = QLabel(strings.DLG_SESSION_NAME_LABEL)
        name_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #454650;")
        layout.addWidget(name_label)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Rural Health Survey Q2")
        layout.addWidget(self._name_edit)

        # File picker
        file_label = QLabel(strings.DLG_IMPORT_FILE_LABEL)
        file_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #454650;")
        layout.addWidget(file_label)

        file_row = QHBoxLayout()
        self._file_display = QLineEdit()
        self._file_display.setReadOnly(True)
        self._file_display.setPlaceholderText("No file selected")
        file_row.addWidget(self._file_display)

        browse_btn = QPushButton(strings.DLG_BROWSE)
        browse_btn.setProperty("class", "secondary")
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setText(strings.BTN_START_SESSION)
        ok_btn.setProperty("class", "primary")
        layout.addWidget(buttons)

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Dataset",
            "",
            "Data Files (*.csv *.tsv *.xlsx *.xls);;All Files (*)",
        )
        if path:
            self._file_path = Path(path)
            self._file_display.setText(self._file_path.name)

    def session_name(self) -> str:
        return self._name_edit.text().strip()

    def file_path(self) -> Path | None:
        return self._file_path
