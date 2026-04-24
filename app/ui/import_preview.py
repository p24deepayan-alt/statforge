"""Import Preview dialog — configure parsing and preview data before starting a session."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QRadioButton,
    QTableView,
    QVBoxLayout,
)

from app.controllers.data_controller import DataController
from app.ui.models.paginated_data_model import PaginatedDataModel
from app.util import strings


class ImportPreviewDialog(QDialog):
    """Full-screen dialog for previewing imported data and configuring parse options."""

    def __init__(
        self,
        file_path: Path,
        data_controller: DataController,
        parent=None,
    ):
        super().__init__(parent)
        self._file_path = file_path
        self._data_ctrl = data_controller
        self._preview_df: pd.DataFrame | None = None

        self.setWindowTitle(strings.IMPORT_TITLE.format(filename=file_path.name))
        self.setMinimumSize(1000, 640)
        self.setModal(True)

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ── Left: Configuration panel ───────────────────────
        config_panel = QFrame()
        config_panel.setObjectName("config_panel")
        config_panel.setFixedWidth(240)
        config_panel.setStyleSheet(
            "QFrame#config_panel { background: #ffffff; border-right: 1px solid #c5c5d2; }"
        )
        config_layout = QVBoxLayout(config_panel)
        config_layout.setContentsMargins(20, 24, 20, 24)
        config_layout.setSpacing(20)

        config_title = QLabel("Configuration")
        config_title.setStyleSheet("font-size: 18px; font-weight: 600; color: #191c1c;")
        config_layout.addWidget(config_title)

        config_hint = QLabel("Adjust parsing rules for this file.")
        config_hint.setWordWrap(True)
        config_hint.setStyleSheet("font-size: 12px; color: #757681;")
        config_layout.addWidget(config_hint)

        # Delimiter
        delim_label = QLabel(strings.CFG_DELIMITER)
        delim_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        config_layout.addWidget(delim_label)

        self._delimiter_combo = QComboBox()
        self._delimiter_combo.addItems(["Comma (,)", "Tab (\\t)", "Semicolon (;)", "Pipe (|)"])
        self._delimiter_combo.currentIndexChanged.connect(self._refresh_preview)
        config_layout.addWidget(self._delimiter_combo)

        # Header row
        header_label = QLabel(strings.CFG_HEADER_ROW)
        header_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        config_layout.addWidget(header_label)

        header_row = QHBoxLayout()
        self._header_yes = QRadioButton("Yes")
        self._header_yes.setChecked(True)
        self._header_no = QRadioButton("No")
        self._header_yes.toggled.connect(self._refresh_preview)
        header_row.addWidget(self._header_yes)
        header_row.addWidget(self._header_no)
        config_layout.addLayout(header_row)

        # Encoding
        enc_label = QLabel(strings.CFG_ENCODING)
        enc_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        config_layout.addWidget(enc_label)

        self._encoding_combo = QComboBox()
        self._encoding_combo.addItems(["UTF-8", "Latin-1", "Windows-1252", "ASCII"])
        self._encoding_combo.currentIndexChanged.connect(self._refresh_preview)
        config_layout.addWidget(self._encoding_combo)

        config_layout.addStretch()

        # File statistics
        stats_frame = QFrame()
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_title = QLabel(strings.FILE_STATS)
        stats_title.setStyleSheet("font-size: 13px; font-weight: 700;")
        stats_layout.addWidget(stats_title)

        try:
            file_size = file_path.stat().st_size
            size_str = self._format_size(file_size)
        except OSError:
            size_str = "?"

        self._stats_labels = {
            "Size:": QLabel(size_str),
            "Rows (est):": QLabel("—"),
            "Columns:": QLabel("—"),
        }
        for k, v in self._stats_labels.items():
            row = QHBoxLayout()
            lbl = QLabel(k)
            lbl.setStyleSheet("font-size: 12px; color: #454650;")
            v.setStyleSheet("font-size: 12px; font-weight: 600; color: #191c1c;")
            v.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(lbl)
            row.addWidget(v)
            stats_layout.addLayout(row)

        config_layout.addWidget(stats_frame)
        main_layout.addWidget(config_panel)

        # ── Right: Preview + actions ─────────────────────────
        right = QVBoxLayout()
        right.setContentsMargins(24, 24, 24, 24)
        right.setSpacing(12)

        preview_title = QLabel(strings.DATA_PREVIEW)
        preview_title.setStyleSheet("font-size: 22px; font-weight: 700; color: #191c1c;")
        right.addWidget(preview_title)

        preview_hint = QLabel(
            strings.DATA_PREVIEW_HINT.format(n=50)
        )
        preview_hint.setWordWrap(True)
        preview_hint.setStyleSheet("font-size: 13px; color: #757681;")
        right.addWidget(preview_hint)

        # Table
        self._table = QTableView()
        self._table_model = PaginatedDataModel()
        self._table.setModel(self._table_model)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.verticalHeader().setDefaultSectionSize(36)
        self._table.setAlternatingRowColors(False)
        right.addWidget(self._table, 1)

        # Bottom buttons
        btn_row = QHBoxLayout()
        back_btn = QPushButton(strings.BTN_BACK)
        back_btn.setProperty("class", "secondary")
        back_btn.clicked.connect(self.reject)
        btn_row.addWidget(back_btn)
        btn_row.addStretch()

        start_btn = QPushButton(strings.BTN_START_SESSION + "  →")
        start_btn.setProperty("class", "primary")
        start_btn.setStyleSheet(
            "QPushButton { background-color: #001857; color: #ffffff; padding: 10px 24px; "
            "font-weight: 600; border-radius: 4px; }"
            "QPushButton:hover { background-color: #1b2f6e; }"
        )
        start_btn.clicked.connect(self.accept)
        btn_row.addWidget(start_btn)
        right.addLayout(btn_row)

        main_layout.addLayout(right, 1)

        # Initial preview
        self._refresh_preview()

    # ── helpers ──────────────────────────────────────────────

    def _current_delimiter(self) -> str:
        mapping = {0: ",", 1: "\t", 2: ";", 3: "|"}
        return mapping.get(self._delimiter_combo.currentIndex(), ",")

    def _current_encoding(self) -> str:
        return self._encoding_combo.currentText().lower().replace("-", "")

    def _refresh_preview(self) -> None:
        try:
            df = self._data_ctrl.preview_file(
                self._file_path,
                delimiter=self._current_delimiter(),
                has_header=self._header_yes.isChecked(),
                encoding=self._current_encoding(),
                nrows=50,
            )
            self._preview_df = df
            self._table_model.set_dataframe(df)
            self._stats_labels["Rows (est):"].setText(f"~{len(df):,}+")
            self._stats_labels["Columns:"].setText(str(len(df.columns)))
        except Exception as exc:
            self._stats_labels["Rows (est):"].setText("Error")
            self._stats_labels["Columns:"].setText("—")

    def get_import_config(self) -> dict[str, Any]:
        return {
            "delimiter": self._current_delimiter(),
            "has_header": self._header_yes.isChecked(),
            "encoding": self._current_encoding(),
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024  # type: ignore[assignment]
        return f"{size_bytes:.1f} TB"
