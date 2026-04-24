"""Sessions Home view — the startup screen showing active sessions."""

from __future__ import annotations

import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.controllers.session_controller import SessionController
from app.util import strings


class SessionsHome(QWidget):
    """The landing page. Lists sessions and handles creation/deletion."""

    session_opened = Signal(str)  # Emitted when the user requests to open a session

    def __init__(self, session_ctrl: SessionController, parent=None):
        super().__init__(parent)
        self._session_ctrl = session_ctrl

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(32)

        # ── Header ───────────────────────────────────────────
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel(strings.SESSIONS_TITLE)
        title.setStyleSheet("font-size: 28px; font-weight: 700; color: #001857;")
        subtitle = QLabel(strings.SESSIONS_SUBTITLE)
        subtitle.setStyleSheet("font-size: 14px; color: #757681;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        self._btn_new = QPushButton(strings.NEW_SESSION)
        self._btn_new.setProperty("class", "primary")
        self._btn_new.setStyleSheet("padding: 10px 24px; font-size: 14px;")
        header.addWidget(self._btn_new)

        layout.addLayout(header)

        # ── Status Cards ─────────────────────────────────────
        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)

        def make_card(title: str, value: str, desc: str) -> QFrame:
            card = QFrame()
            card.setProperty("class", "card")
            lyt = QVBoxLayout(card)
            t = QLabel(title)
            t.setStyleSheet("font-size: 12px; font-weight: 700; color: #757681; text-transform: uppercase; background-color: transparent;")
            v = QLabel(value)
            v.setStyleSheet("font-size: 24px; font-weight: 700; color: #001857; margin-top: 8px; background-color: transparent;")
            d = QLabel(desc)
            d.setStyleSheet("font-size: 12px; color: #757681; background-color: transparent;")
            lyt.addWidget(t)
            lyt.addWidget(v)
            lyt.addWidget(d)
            return card

        self._card_active = make_card(strings.ACTIVE_SESSIONS, "0", "Local workspace datasets")
        self._card_storage = make_card(strings.LOCAL_STORAGE, "0 MB", "Total disk space used")
        card_sys = make_card(strings.SYSTEM_STATUS, strings.OFFLINE_READY, strings.OFFLINE_DETAIL)

        cards_layout.addWidget(self._card_active, 0, 0)
        cards_layout.addWidget(self._card_storage, 0, 1)
        cards_layout.addWidget(card_sys, 0, 2)
        
        layout.addLayout(cards_layout)

        # ── Table ────────────────────────────────────────────
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels([
            strings.COL_SESSION_NAME,
            strings.COL_SOURCE_DATASET,
            strings.COL_CREATED,
            strings.COL_MODIFIED,
            strings.COL_ACTIONS
        ])
        header = self._table.horizontalHeader()
        header.setStretchLastSection(False)
        # Session Name: stretches to fill remaining space
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        # Source Dataset: stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # Created: fixed
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self._table.setColumnWidth(2, 140)
        # Modified: fixed
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self._table.setColumnWidth(3, 140)
        # Actions: fixed
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self._table.setColumnWidth(4, 160)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(50)  # Make rows tall enough for buttons
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.cellDoubleClicked.connect(self._on_double_click)

        layout.addWidget(self._table, 1)

        # Initial load
        self.refresh()
        self._session_ctrl.sessions_changed.connect(self.refresh)

    def refresh(self) -> None:
        """Reload the sessions list and update metrics."""
        sessions = self._session_ctrl.list_sessions()
        
        # Update cards
        count = len(sessions)
        
        # Real card updates:
        self._card_active.layout().itemAt(1).widget().setText(str(count))
        
        size_bytes = self._session_ctrl.storage_size_bytes()
        size_mb = size_bytes / (1024 * 1024)
        self._card_storage.layout().itemAt(1).widget().setText(f"{size_mb:.1f} MB")

        # Update table
        self._table.setRowCount(0)
        for i, sess in enumerate(sessions):
            self._table.insertRow(i)
            
            # Session Name
            name_item = QTableWidgetItem(sess["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, sess["id"])  # Store ID
            self._table.setItem(i, 0, name_item)
            
            # Source Dataset
            self._table.setItem(i, 1, QTableWidgetItem(sess["source_filename"] or "—"))
            
            # Created
            dt_c = datetime.datetime.fromisoformat(sess["created_at"])
            self._table.setItem(i, 2, QTableWidgetItem(dt_c.strftime("%Y-%m-%d %H:%M")))
            
            # Modified
            dt_m = datetime.datetime.fromisoformat(sess["modified_at"])
            self._table.setItem(i, 3, QTableWidgetItem(dt_m.strftime("%Y-%m-%d %H:%M")))
            
            # Actions
            btn_box = QWidget()
            btn_lyt = QHBoxLayout(btn_box)
            btn_lyt.setContentsMargins(4, 4, 4, 4)
            btn_lyt.setSpacing(8)
            
            open_btn = QPushButton("Open")
            open_btn.setProperty("class", "secondary")
            open_btn.clicked.connect(lambda checked, sid=sess["id"]: self.session_opened.emit(sid))
            
            del_btn = QPushButton("Delete")
            del_btn.setProperty("class", "ghost")
            del_btn.clicked.connect(lambda checked, sid=sess["id"]: self._delete_session(sid))
            
            btn_lyt.addWidget(open_btn)
            btn_lyt.addWidget(del_btn)
            btn_lyt.addStretch()
            
            self._table.setCellWidget(i, 4, btn_box)

    def _on_double_click(self, row: int, col: int) -> None:
        item = self._table.item(row, 0)
        if item:
            session_id = item.data(Qt.ItemDataRole.UserRole)
            self.session_opened.emit(session_id)

    def _delete_session(self, session_id: str) -> None:
        sess = self._session_ctrl.get_session(session_id)
        if not sess:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the session '{sess['name']}'?\n"
            "This will permanently delete the dataset, models, and reports.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._session_ctrl.delete_session(session_id)
