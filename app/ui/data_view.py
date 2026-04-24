"""Data View panel — paginated spreadsheet with descriptive statistics."""

from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.controllers.data_controller import DataController
from app.ui.models.paginated_data_model import PaginatedDataModel
from app.util import strings


class DataView(QWidget):
    """Shows the dataset and a side panel with column statistics."""

    def __init__(self, data_ctrl: DataController, parent=None):
        super().__init__(parent)
        self._data_ctrl = data_ctrl
        self._session_id: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ── Left: Spreadsheet ────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel(strings.DATASET_VIEW)
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #191c1c;")
        header_row.addWidget(title)
        header_row.addStretch()

        # Pagination controls
        self._page_label = QLabel("—")
        self._page_label.setStyleSheet("font-size: 13px; color: #757681;")
        header_row.addWidget(self._page_label)

        self._btn_prev = QPushButton("←")
        self._btn_prev.setProperty("class", "secondary")
        self._btn_prev.setFixedWidth(40)
        self._btn_prev.clicked.connect(self._on_prev_page)
        header_row.addWidget(self._btn_prev)

        self._btn_next = QPushButton("→")
        self._btn_next.setProperty("class", "secondary")
        self._btn_next.setFixedWidth(40)
        self._btn_next.clicked.connect(self._on_next_page)
        header_row.addWidget(self._btn_next)

        lbl_size = QLabel(strings.ROWS_PER_PAGE)
        lbl_size.setStyleSheet("font-size: 13px; color: #757681; margin-left: 16px;")
        header_row.addWidget(lbl_size)

        self._combo_size = QComboBox()
        self._combo_size.addItems([str(sz) for sz in PaginatedDataModel.PAGE_SIZES])
        self._combo_size.currentTextChanged.connect(self._on_page_size_changed)
        header_row.addWidget(self._combo_size)

        left.addLayout(header_row)

        self._table = QTableView()
        self._model = PaginatedDataModel()
        self._table.setModel(self._model)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.verticalHeader().setDefaultSectionSize(36)
        self._table.setAlternatingRowColors(False)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._table.viewport().installEventFilter(self)
        left.addWidget(self._table)

        layout.addLayout(left, stretch=1)

        # ── Right: Stats Panel ───────────────────────────────
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        right_scroll.setStyleSheet("background: transparent;")
        
        self._stats_container = QWidget()
        self._stats_layout = QVBoxLayout(self._stats_container)
        self._stats_layout.setContentsMargins(0, 0, 0, 0)
        self._stats_layout.setSpacing(16)
        self._stats_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        stats_title = QLabel(strings.DESCRIPTIVE_STATS)
        stats_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1b2f6e;")
        self._stats_layout.addWidget(stats_title)

        self._stats_placeholder = QLabel("Select a column to view statistics.")
        self._stats_placeholder.setStyleSheet("font-size: 13px; color: #757681;")
        self._stats_layout.addWidget(self._stats_placeholder)
        
        self._dynamic_stats_container = None
        self._stats_layout.addStretch()

        right_scroll.setWidget(self._stats_container)
        right_scroll.setFixedWidth(280)
        layout.addWidget(right_scroll)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Redirect Shift+scroll to horizontal scrollbar."""
        if obj is self._table.viewport() and isinstance(event, QWheelEvent):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                sb = self._table.horizontalScrollBar()
                delta = event.angleDelta().y()
                sb.setValue(sb.value() - delta)
                return True
        return super().eventFilter(obj, event)

    def load_session(self, session_id: str) -> None:
        self._session_id = session_id
        df = self._data_ctrl.load_dataset(session_id)
        self._model.set_dataframe(df)
        self._update_pagination_ui()
        self._clear_stats()

    def _on_prev_page(self) -> None:
        self._model.set_page(self._model.current_page - 1)
        self._update_pagination_ui()

    def _on_next_page(self) -> None:
        self._model.set_page(self._model.current_page + 1)
        self._update_pagination_ui()

    def _on_page_size_changed(self, text: str) -> None:
        size = int(text)
        self._model.set_page_size(size)
        self._update_pagination_ui()

    def _update_pagination_ui(self) -> None:
        self._page_label.setText(self._model.page_label())
        self._btn_prev.setEnabled(self._model.current_page > 0)
        self._btn_next.setEnabled(self._model.current_page < self._model.page_count() - 1)

    def _on_selection_changed(self) -> None:
        indexes = self._table.selectionModel().selectedIndexes()
        if not indexes:
            self._clear_stats()
            return

        # Use the column of the first selected cell.
        col_idx = indexes[0].column()
        col_name = str(self._model.dataframe.columns[col_idx])
        
        if self._session_id:
            stats = self._data_ctrl.get_column_stats(self._session_id, col_name)
            self._render_stats(stats)

    def _clear_stats(self) -> None:
        if hasattr(self, '_dynamic_stats_container') and self._dynamic_stats_container:
            self._dynamic_stats_container.deleteLater()
            self._dynamic_stats_container = None
        self._stats_placeholder.show()

    def _render_stats(self, stats: dict[str, Any]) -> None:
        self._clear_stats()
        self._stats_placeholder.hide()

        self._dynamic_stats_container = QWidget()
        dyn_lyt = QVBoxLayout(self._dynamic_stats_container)
        dyn_lyt.setContentsMargins(0, 0, 0, 0)
        dyn_lyt.setSpacing(16)

        name_lbl = QLabel(stats["name"])
        name_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #191c1c;")
        dyn_lyt.addWidget(name_lbl)

        # Meta tags
        meta_row = QHBoxLayout()
        meta_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        dtype_chip = QLabel(stats["dtype"])
        dtype_chip.setProperty("class", "chip_primary")
        meta_row.addWidget(dtype_chip)
        
        type_chip = QLabel("Numeric" if stats.get("is_numeric") else "Categorical")
        type_chip.setProperty("class", "chip")
        meta_row.addWidget(type_chip)
        dyn_lyt.addLayout(meta_row)

        # Grid of cards
        grid = QFrame()
        grid_layout = QVBoxLayout(grid)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(8)

        def add_card(label: str, value: Any) -> None:
            card = QFrame()
            card.setProperty("class", "stat_card")
            lyt = QHBoxLayout(card)
            lyt.setContentsMargins(12, 12, 12, 12)
            lbl = QLabel(label)
            lbl.setProperty("class", "stat_label")
            val = QLabel(str(value))
            val.setProperty("class", "stat_value")
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lyt.addWidget(lbl)
            lyt.addWidget(val)
            grid_layout.addWidget(card)

        add_card(strings.STAT_COUNT, f"{stats['count']:,}")
        missing_str = f"{stats['missing']:,} ({stats['missing_pct']}%)"
        add_card(strings.STAT_MISSING, missing_str)
        add_card(strings.STAT_UNIQUE, f"{stats['unique']:,}")

        if stats.get("is_numeric"):
            add_card(strings.STAT_MEAN, stats.get("mean"))
            add_card(strings.STAT_MEDIAN, stats.get("median"))
            add_card(strings.STAT_STD_DEV, stats.get("std"))
            add_card(strings.STAT_MIN, stats.get("min"))
            add_card(strings.STAT_MAX, stats.get("max"))
        else:
            mode_str = f"{stats.get('mode', '—')} ({stats.get('mode_pct', 0)}%)"
            add_card(strings.STAT_MODE, mode_str)

        dyn_lyt.addWidget(grid)
        
        # Action button
        btn_add = QPushButton(strings.ADD_TO_REPORT)
        btn_add.setProperty("class", "secondary")
        dyn_lyt.addWidget(btn_add)
        
        # Insert before the stretch
        self._stats_layout.insertWidget(2, self._dynamic_stats_container)
