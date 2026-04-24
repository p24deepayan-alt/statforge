"""Preprocessing pipeline view."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.controllers.data_controller import DataController
from app.controllers.preprocessing_controller import PreprocessingController
from app.util import strings


class PreprocessingView(QWidget):
    """UI for building the preprocessing pipeline and viewing history."""

    def __init__(
        self, data_ctrl: DataController, prep_ctrl: PreprocessingController, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._data_ctrl = data_ctrl
        self._prep_ctrl = prep_ctrl
        self._session_id: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ── Left: Operation Builder ──────────────────────────
        left_panel = QFrame()
        left_panel.setProperty("class", "card")
        left_lyt = QVBoxLayout(left_panel)
        left_lyt.setSpacing(16)

        title = QLabel("Add Operation")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #191c1c;")
        left_lyt.addWidget(title)

        # Op selector
        op_row = QHBoxLayout()
        op_lbl = QLabel("Operation Type:")
        self._op_combo = QComboBox()
        self._op_combo.addItems(["Impute Missing Values", "Scale / Normalize", "Encode Categorical", "Drop Column", "Drop NA Rows"])
        self._op_combo.currentIndexChanged.connect(self._on_op_changed)
        op_row.addWidget(op_lbl)
        op_row.addWidget(self._op_combo, 1)
        left_lyt.addLayout(op_row)

        left_lyt.addWidget(self._create_separator())

        # Column selector — multi-select with checkboxes
        col_lbl_row = QHBoxLayout()
        col_lbl_row.addWidget(QLabel("Target Columns:"))
        col_lbl_row.addStretch()
        
        self._btn_select_all = QPushButton("Select All")
        self._btn_select_all.setStyleSheet("font-size: 12px; padding: 4px 10px;")
        self._btn_select_all.clicked.connect(self._select_all_cols)
        col_lbl_row.addWidget(self._btn_select_all)
        
        self._btn_deselect_all = QPushButton("Deselect All")
        self._btn_deselect_all.setStyleSheet("font-size: 12px; padding: 4px 10px;")
        self._btn_deselect_all.clicked.connect(self._deselect_all_cols)
        col_lbl_row.addWidget(self._btn_deselect_all)
        
        left_lyt.addLayout(col_lbl_row)
        
        self._col_list = QListWidget()
        self._col_list.setStyleSheet(
            "QListWidget::indicator { width: 16px; height: 16px; border: 1px solid #000000; border-radius: 2px; }"
            "QListWidget::indicator:checked { background-color: #001857; }"
        )
        self._col_list.setMaximumHeight(150)
        left_lyt.addWidget(self._col_list)

        # Operation-specific forms
        self._stack = QStackedWidget()
        
        # 0: Impute
        self._form_impute = QWidget()
        im_lyt = QVBoxLayout(self._form_impute)
        im_lyt.setContentsMargins(0, 0, 0, 0)
        self._impute_strat = QComboBox()
        self._impute_strat.addItems(["mean", "median", "mode", "constant"])
        self._impute_const = QLineEdit()
        self._impute_const.setPlaceholderText("Fill value (if constant)")
        self._impute_const.setEnabled(False)
        self._impute_strat.currentTextChanged.connect(
            lambda t: self._impute_const.setEnabled(t == "constant")
        )
        im_lyt.addWidget(QLabel("Strategy:"))
        im_lyt.addWidget(self._impute_strat)
        im_lyt.addWidget(self._impute_const)
        im_lyt.addStretch()
        self._stack.addWidget(self._form_impute)

        # 1: Scale
        self._form_scale = QWidget()
        sc_lyt = QVBoxLayout(self._form_scale)
        sc_lyt.setContentsMargins(0, 0, 0, 0)
        self._scale_method = QComboBox()
        self._scale_method.addItems(["standard", "minmax"])
        sc_lyt.addWidget(QLabel("Method:"))
        sc_lyt.addWidget(self._scale_method)
        sc_lyt.addStretch()
        self._stack.addWidget(self._form_scale)

        # 2: Encode
        self._form_encode = QWidget()
        en_lyt = QVBoxLayout(self._form_encode)
        en_lyt.setContentsMargins(0, 0, 0, 0)
        self._encode_method = QComboBox()
        self._encode_method.addItems(["label", "onehot"])
        en_lyt.addWidget(QLabel("Method:"))
        en_lyt.addWidget(self._encode_method)
        en_lyt.addStretch()
        self._stack.addWidget(self._form_encode)

        # 3: Drop Column
        self._form_drop_col = QWidget()
        dc_lyt = QVBoxLayout(self._form_drop_col)
        dc_lyt.setContentsMargins(0, 0, 0, 0)
        dc_lyt.addWidget(QLabel("Will drop the selected target column."))
        dc_lyt.addStretch()
        self._stack.addWidget(self._form_drop_col)

        # 4: Drop NA
        self._form_drop_na = QWidget()
        dn_lyt = QVBoxLayout(self._form_drop_na)
        dn_lyt.setContentsMargins(0, 0, 0, 0)
        dn_lyt.addWidget(QLabel("Will drop all rows containing NA in the target column."))
        dn_lyt.addStretch()
        self._stack.addWidget(self._form_drop_na)

        left_lyt.addWidget(self._stack, 1)

        # Apply Button
        self._btn_apply = QPushButton("Apply Operation")
        self._btn_apply.setProperty("class", "primary")
        self._btn_apply.clicked.connect(self._on_apply)
        left_lyt.addWidget(self._btn_apply)

        layout.addWidget(left_panel, 1)

        # ── Right: Pipeline History ──────────────────────────
        right_panel = QVBoxLayout()
        right_panel.setSpacing(16)

        hist_header = QHBoxLayout()
        hist_title = QLabel("Pipeline History")
        hist_title.setStyleSheet("font-size: 18px; font-weight: 600; color: #191c1c;")
        self._btn_undo = QPushButton("Undo Last Step")
        self._btn_undo.setProperty("class", "secondary")
        self._btn_undo.clicked.connect(self._on_undo)
        hist_header.addWidget(hist_title)
        hist_header.addStretch()
        hist_header.addWidget(self._btn_undo)
        right_panel.addLayout(hist_header)

        self._history_list = QListWidget()
        self._history_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._history_list.setStyleSheet(
            "QListWidget { background: #ffffff; border: 1px solid #c5c5d2; border-radius: 4px; padding: 8px; }"
            "QListWidget::item { padding: 8px; border-bottom: 1px solid #e6e9e8; }"
        )
        right_panel.addWidget(self._history_list)

        layout.addLayout(right_panel, 1)

        # Connect error handler
        self._prep_ctrl.error_occurred.connect(self._show_error)

    def load_session(self, session_id: str) -> None:
        self._session_id = session_id
        self._refresh_columns()
        self._refresh_history()

    def _refresh_columns(self) -> None:
        if not self._session_id:
            return
        df = self._data_ctrl.load_dataset(self._session_id)
        
        # Remember checked columns
        checked = set()
        for i in range(self._col_list.count()):
            item = self._col_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked.add(item.text())
        
        self._col_list.clear()
        for c in df.columns:
            item = QListWidgetItem(str(c))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if str(c) in checked else Qt.CheckState.Unchecked)
            self._col_list.addItem(item)

    def _select_all_cols(self) -> None:
        for i in range(self._col_list.count()):
            self._col_list.item(i).setCheckState(Qt.CheckState.Checked)

    def _deselect_all_cols(self) -> None:
        for i in range(self._col_list.count()):
            self._col_list.item(i).setCheckState(Qt.CheckState.Unchecked)

    def _refresh_history(self) -> None:
        if not self._session_id:
            return
        self._history_list.clear()
        steps = self._prep_ctrl.get_steps(self._session_id)
        if not steps:
            self._history_list.addItem("Pipeline is empty. Original dataset is unmodified.")
        else:
            for step in steps:
                self._history_list.addItem(f"{step['step_index'] + 1}. {step['description']}")
        
        self._btn_undo.setEnabled(self._prep_ctrl.can_undo(self._session_id))

    def _on_op_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)

    def _on_apply(self) -> None:
        if not self._session_id:
            return

        op_idx = self._op_combo.currentIndex()
        
        # Gather selected columns
        selected_cols = []
        for i in range(self._col_list.count()):
            item = self._col_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_cols.append(item.text())

        if not selected_cols:
            self._show_error("No target columns selected.")
            return

        try:
            self._btn_apply.setEnabled(False)
            
            for col in selected_cols:
                op_name = ""
                params: dict[str, Any] = {"column": col}
                desc = ""

                if op_idx == 0:  # Impute
                    op_name = "impute"
                    strat = self._impute_strat.currentText()
                    params["strategy"] = strat
                    if strat == "constant":
                        params["fill_value"] = self._impute_const.text()
                    desc = f"Impute missing values in '{col}' using {strat}"

                elif op_idx == 1:  # Scale
                    op_name = "scale"
                    method = self._scale_method.currentText()
                    params["method"] = method
                    desc = f"Scale '{col}' using {method} scaler"

                elif op_idx == 2:  # Encode
                    op_name = "encode"
                    method = self._encode_method.currentText()
                    params["method"] = method
                    desc = f"Encode '{col}' using {method} encoding"

                elif op_idx == 3:  # Drop Column
                    op_name = "drop_column"
                    desc = f"Drop column '{col}'"

                elif op_idx == 4:  # Drop NA
                    op_name = "drop_na"
                    params = {"subset": [col]}
                    desc = f"Drop rows with NA in '{col}'"

                self._prep_ctrl.apply_step(self._session_id, op_name, params, desc)
            
            self._refresh_columns()
            self._refresh_history()
        finally:
            self._btn_apply.setEnabled(True)

    def _on_undo(self) -> None:
        if not self._session_id:
            return
        try:
            self._btn_undo.setEnabled(False)
            self._prep_ctrl.undo_last_step(self._session_id)
            self._refresh_columns()
            self._refresh_history()
        finally:
            self._btn_undo.setEnabled(True)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Preprocessing Error", message)

    @staticmethod
    def _create_separator() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #c5c5d2;")
        return line
