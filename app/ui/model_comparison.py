"""Model Comparison View."""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.controllers.model_controller import ModelController
from app.controllers.comparison_controller import ComparisonController


class ModelComparisonView(QWidget):
    """UI for comparing performance metrics across trained models."""

    def __init__(self, model_ctrl: ModelController, comp_ctrl: ComparisonController, parent: QWidget | None = None):
        super().__init__(parent)
        self._model_ctrl = model_ctrl
        self._comp_ctrl = comp_ctrl
        self._session_id: str | None = None
        self._all_models: list[dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_lyt = QHBoxLayout()
        title = QLabel("Model Comparison")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #191c1c;")
        header_lyt.addWidget(title)

        header_lyt.addStretch()

        header_lyt.addWidget(QLabel("Filter by Target:"))
        self._target_filter = QComboBox()
        self._target_filter.currentTextChanged.connect(self._render_table)
        header_lyt.addWidget(self._target_filter)

        layout.addLayout(header_lyt)

        self._table = QTableWidget()
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        self._table.setStyleSheet(
            "QTableWidget { background: #ffffff; border: 1px solid #c5c5d2; border-radius: 4px; }"
            "QHeaderView::section { background: #f2f4f3; padding: 4px; font-weight: bold; border: none; border-bottom: 1px solid #c5c5d2; }"
        )
        layout.addWidget(self._table, 2)
        
        # Bottom area for comparison actions
        bottom_lyt = QHBoxLayout()
        from PySide6.QtWidgets import QPushButton, QMessageBox
        
        self._btn_roc = QPushButton("Generate ROC Curve for Selected Models")
        self._btn_roc.setProperty("class", "primary")
        self._btn_roc.clicked.connect(self._on_generate_roc)
        bottom_lyt.addWidget(self._btn_roc)
        bottom_lyt.addStretch()
        
        layout.addLayout(bottom_lyt)
        
        self._comp_ctrl.error_occurred.connect(self._show_error)
        self._comp_ctrl.comparison_created.connect(self._on_comparison_created)

    def _show_error(self, msg: str) -> None:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Comparison Error", msg)
        
    def _on_generate_roc(self) -> None:
        if not self._session_id:
            return
            
        selected_model_ids = []
        for row in range(self._table.rowCount()):
            chk_item = self._table.item(row, 0)
            if chk_item and chk_item.checkState() == Qt.CheckState.Checked:
                model_id = chk_item.data(Qt.ItemDataRole.UserRole)
                selected_model_ids.append(model_id)
                
        if not selected_model_ids:
            self._show_error("Please select at least one model to compare.")
            return
            
        self._btn_roc.setEnabled(False)
        self._btn_roc.setText("Generating...")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            self._comp_ctrl.generate_roc_comparison(self._session_id, selected_model_ids)
        finally:
            self._btn_roc.setEnabled(True)
            self._btn_roc.setText("Generate ROC Curve for Selected Models")
            
    def _on_comparison_created(self, artifact_id: str) -> None:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Success", "ROC Curve generated and added to artifacts!")

    def load_session(self, session_id: str) -> None:
        self._session_id = session_id
        self._refresh()

    def _refresh(self) -> None:
        if not self._session_id:
            return
            
        self._all_models = self._model_ctrl.get_models(self._session_id)
        
        # Extract unique targets
        targets = set()
        for m in self._all_models:
            spec = json.loads(m["spec_json"])
            t = spec.get("target")
            if t:
                targets.add(t)
        
        curr_t = self._target_filter.currentText()
        self._target_filter.blockSignals(True)
        self._target_filter.clear()
        self._target_filter.addItem("All Targets")
        for t in sorted(targets):
            self._target_filter.addItem(t)
            
        idx = self._target_filter.findText(curr_t)
        if idx >= 0:
            self._target_filter.setCurrentIndex(idx)
        else:
            self._target_filter.setCurrentIndex(0)
            
        self._target_filter.blockSignals(False)
        self._render_table()

    def _render_table(self) -> None:
        self._table.clear()
        self._table.setRowCount(0)
        
        if not self._all_models:
            self._table.setColumnCount(1)
            self._table.setHorizontalHeaderLabels(["No Models Trained"])
            return

        filter_t = self._target_filter.currentText()

        # Filter models
        filtered = []
        all_metrics = set()
        for m in self._all_models:
            spec = json.loads(m["spec_json"])
            target = spec.get("target")
            if filter_t == "All Targets" or target == filter_t:
                filtered.append((m, spec))
                for k in spec.get("metrics", {}).keys():
                    all_metrics.add(k)

        if not filtered:
            self._table.setColumnCount(1)
            self._table.setHorizontalHeaderLabels(["No models match filter"])
            return

        # Prepare headers
        metrics_headers = sorted(list(all_metrics))
        headers = ["Name", "Algorithm", "Target"] + metrics_headers
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)

        # Populate rows
        self._table.setRowCount(len(filtered))
        for row_idx, (m, spec) in enumerate(filtered):
            
            # Name with checkbox
            item_name = QTableWidgetItem(m["name"])
            item_name.setFlags(item_name.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item_name.setCheckState(Qt.CheckState.Unchecked)
            item_name.setData(Qt.ItemDataRole.UserRole, m["id"])
            self._table.setItem(row_idx, 0, item_name)
            
            # Algorithm
            item_algo = QTableWidgetItem(spec.get("model_type", "N/A"))
            self._table.setItem(row_idx, 1, item_algo)
            
            # Target
            item_target = QTableWidgetItem(spec.get("target", "N/A"))
            self._table.setItem(row_idx, 2, item_target)
            
            # Metrics
            metrics = spec.get("metrics", {})
            for col_idx, met_name in enumerate(metrics_headers):
                val = metrics.get(met_name, "")
                if isinstance(val, float):
                    item_val = QTableWidgetItem(f"{val:.4f}")
                else:
                    item_val = QTableWidgetItem(str(val))
                self._table.setItem(row_idx, col_idx + 3, item_val)
