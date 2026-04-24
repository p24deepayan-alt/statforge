"""Paginated Qt table model backed by a pandas DataFrame.

Only the visible page is materialised into Qt's model layer, keeping memory
usage constant regardless of dataset size.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class PaginatedDataModel(QAbstractTableModel):
    """Shows one page of a DataFrame at a time."""

    PAGE_SIZES = [100, 200, 500]

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._df: pd.DataFrame = pd.DataFrame()
        self._page: int = 0
        self._page_size: int = 100
        
        # Cache for the current page to speed up rendering
        self._page_cache: Any = None

    # ── public API ───────────────────────────────────────────

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df
        self._page = 0
        self._update_cache()
        self.endResetModel()

    def set_page(self, page: int) -> None:
        page = max(0, min(page, self.page_count() - 1))
        if page != self._page:
            self.beginResetModel()
            self._page = page
            self._update_cache()
            self.endResetModel()

    def set_page_size(self, size: int) -> None:
        if size in self.PAGE_SIZES and size != self._page_size:
            self.beginResetModel()
            self._page_size = size
            self._page = 0
            self._update_cache()
            self.endResetModel()

    def _update_cache(self) -> None:
        if len(self._df) == 0:
            self._page_cache = None
            return
        start = self._page * self._page_size
        end = start + self._page_size
        self._page_cache = self._df.iloc[start:end].values

    @property
    def current_page(self) -> int:
        return self._page

    @property
    def page_size(self) -> int:
        return self._page_size

    def page_count(self) -> int:
        if len(self._df) == 0:
            return 1
        return max(1, -(-len(self._df) // self._page_size))  # ceil division

    def total_rows(self) -> int:
        return len(self._df)

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._df

    def page_label(self) -> str:
        """Human-readable label like '1-500 of 14,250'."""
        start = self._page * self._page_size + 1
        end = min(start + self._page_size - 1, len(self._df))
        total = f"{len(self._df):,}"
        return f"{start:,}-{end:,} of {total}"

    # ── Qt model interface ───────────────────────────────────

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        start = self._page * self._page_size
        return min(self._page_size, max(0, len(self._df) - start))

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            if self._page_cache is None:
                return ""
            row = index.row()
            col = index.column()
            val = self._page_cache[row, col]
            if pd.isna(val):
                return ""
            return str(val)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            col = index.column()
            if pd.api.types.is_numeric_dtype(self._df.iloc[:, col]):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        # Vertical header: show absolute row number
        return str(self._page * self._page_size + section + 1)
