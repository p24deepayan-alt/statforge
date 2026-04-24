"""Machine Learning modeling view."""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import pandas as pd

from app.controllers.data_controller import DataController
from app.controllers.model_controller import ModelController
from app.util import strings


class ModelingView(QWidget):
    """UI for defining, training, and viewing ML models."""

    def __init__(
        self, data_ctrl: DataController, model_ctrl: ModelController, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._data_ctrl = data_ctrl
        self._model_ctrl = model_ctrl
        self._session_id: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ── Left: Model Builder ──────────────────────────────
        left_panel = QFrame()
        left_panel.setProperty("class", "card")
        left_panel.setFixedWidth(350)
        left_lyt = QVBoxLayout(left_panel)
        left_lyt.setSpacing(16)

        title = QLabel("Train New Model")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #191c1c;")
        left_lyt.addWidget(title)

        # Name
        left_lyt.addWidget(QLabel("Model Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Baseline OLS")
        left_lyt.addWidget(self._name_edit)

        # Type
        left_lyt.addWidget(QLabel("Algorithm:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems([
            "ols", "logistic", "rf_regressor", "rf_classifier", "kmeans"
        ])
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        left_lyt.addWidget(self._type_combo)

        # Target
        self._lbl_target = QLabel("Target Variable (Y):")
        left_lyt.addWidget(self._lbl_target)
        self._target_combo = QComboBox()
        self._target_combo.currentTextChanged.connect(self._on_target_changed)
        left_lyt.addWidget(self._target_combo)

        # Features
        feat_lbl_lyt = QHBoxLayout()
        feat_lbl_lyt.addWidget(QLabel("Features (X):"))
        feat_lbl_lyt.addStretch()
        
        self._btn_sel_all = QPushButton("All")
        self._btn_sel_all.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        self._btn_sel_all.clicked.connect(self._select_all_features)
        feat_lbl_lyt.addWidget(self._btn_sel_all)

        self._btn_desel_all = QPushButton("None")
        self._btn_desel_all.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        self._btn_desel_all.clicked.connect(self._deselect_all_features)
        feat_lbl_lyt.addWidget(self._btn_desel_all)
        
        self._btn_add_interaction = QPushButton("Add Interaction")
        self._btn_add_interaction.setProperty("class", "secondary")
        self._btn_add_interaction.clicked.connect(self._on_add_interaction)
        # feat_lbl_lyt.addWidget(self._btn_add_interaction)  # Removed from here
        
        left_lyt.addLayout(feat_lbl_lyt)
        self._features_list = QListWidget()
        self._features_list.setStyleSheet(
            "QListWidget::indicator { width: 16px; height: 16px; border: 1px solid #000000; border-radius: 2px; }"
            "QListWidget::indicator:checked { background-color: #001857; }"
        )
        left_lyt.addWidget(self._features_list, 1) # Takes up remaining space
        left_lyt.addWidget(self._btn_add_interaction)

        # Hyperparameters Stack
        self._params_stack = QStackedWidget()
        self._params_stack.setFixedHeight(80)
        
        # Empty for OLS/Logistic
        self._params_stack.addWidget(QWidget()) 
        
        # RF Params
        rf_widget = QWidget()
        rf_lyt = QVBoxLayout(rf_widget)
        rf_lyt.setContentsMargins(0,0,0,0)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("n_estimators:"))
        self._rf_est = QSpinBox()
        self._rf_est.setRange(10, 1000)
        self._rf_est.setValue(100)
        row1.addWidget(self._rf_est)
        rf_lyt.addLayout(row1)
        self._params_stack.addWidget(rf_widget)
        
        # KMeans Params
        km_widget = QWidget()
        km_lyt = QVBoxLayout(km_widget)
        km_lyt.setContentsMargins(0,0,0,0)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("n_clusters:"))
        self._km_k = QSpinBox()
        self._km_k.setRange(2, 50)
        self._km_k.setValue(3)
        row2.addWidget(self._km_k)
        km_lyt.addLayout(row2)
        self._params_stack.addWidget(km_widget)

        left_lyt.addWidget(self._params_stack)

        btn_lyt = QHBoxLayout()
        self._btn_train = QPushButton("Train Model")
        self._btn_train.setProperty("class", "primary")
        self._btn_train.clicked.connect(self._on_train)
        btn_lyt.addWidget(self._btn_train)
        
        self._btn_best = QPushButton("Find Best Model")
        self._btn_best.setProperty("class", "secondary")
        self._btn_best.clicked.connect(self._on_find_best)
        btn_lyt.addWidget(self._btn_best)
        
        left_lyt.addLayout(btn_lyt)

        layout.addWidget(left_panel)

        # ── Center: Models List & Metrics ──────────────────────
        center_panel_frame = QFrame()
        center_panel_frame.setFixedWidth(350)
        center_panel = QVBoxLayout(center_panel_frame)
        center_panel.setContentsMargins(0, 0, 0, 0)
        center_panel.setSpacing(16)
        
        center_hdr_lyt = QHBoxLayout()
        center_header = QLabel("Trained Models")
        center_header.setStyleSheet("font-size: 18px; font-weight: 600; color: #191c1c;")
        center_hdr_lyt.addWidget(center_header)
        
        self._btn_delete_model = QPushButton("Delete")
        self._btn_delete_model.setProperty("class", "ghost")
        self._btn_delete_model.setEnabled(False)
        self._btn_delete_model.clicked.connect(self._on_delete_model)
        center_hdr_lyt.addWidget(self._btn_delete_model)
        
        center_panel.addLayout(center_hdr_lyt)

        self._models_list = QListWidget()
        self._models_list.setStyleSheet(
            "QListWidget { background: #ffffff; border: 1px solid #c5c5d2; border-radius: 4px; padding: 4px; }"
            "QListWidget::item { padding: 12px; border-bottom: 1px solid #e6e9e8; }"
            "QListWidget::item:selected { background: #dce1ff; color: #001857; }"
        )
        self._models_list.itemSelectionChanged.connect(self._on_model_select)
        center_panel.addWidget(self._models_list, 1)
        
        layout.addWidget(center_panel_frame)

        # ── Right: Details Panel ─────────────────────────────
        right_panel = QFrame()
        right_panel.setProperty("class", "card")
        right_lyt = QVBoxLayout(right_panel)
        right_lyt.setSpacing(12)
        
        det_header = QLabel("Model Details")
        det_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #191c1c;")
        right_lyt.addWidget(det_header)
        
        self._details_lbl = QLabel("Select a model to view details.")
        self._details_lbl.setWordWrap(True)
        self._details_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._details_lbl)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        right_lyt.addWidget(scroll, 1)
        
        layout.addWidget(right_panel, 1)

        self._model_ctrl.error_occurred.connect(self._show_error)

    # ── Logic ────────────────────────────────────────────────

    def _select_all_features(self) -> None:
        for i in range(self._features_list.count()):
            item = self._features_list.item(i)
            # Do not check the target variable if it's currently selected in the combo
            if item.text() != self._target_combo.currentText():
                item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all_features(self) -> None:
        for i in range(self._features_list.count()):
            self._features_list.item(i).setCheckState(Qt.CheckState.Unchecked)

    def load_session(self, session_id: str) -> None:
        self._session_id = session_id
        self._refresh_columns()
        self._refresh_models()

    def _refresh_columns(self) -> None:
        if not self._session_id:
            return
        df = self._data_ctrl.load_dataset(self._session_id)
        cols = list(df.columns)
        
        # Target
        curr_t = self._target_combo.currentText()
        self._target_combo.blockSignals(True)
        self._target_combo.clear()
        self._target_combo.addItems([""] + cols)
        idx = self._target_combo.findText(curr_t)
        if idx >= 0:
            self._target_combo.setCurrentIndex(idx)
        self._target_combo.blockSignals(False)

        # Features
        # Remember checked
        checked = set()
        for i in range(self._features_list.count()):
            item = self._features_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked.add(item.text())
                
        self._features_list.clear()
        for c in cols:
            item = QListWidgetItem(c)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            if c == curr_t and self._target_combo.isEnabled():
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(Qt.CheckState.Unchecked)
            elif c in checked:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
                
            self._features_list.addItem(item)

        self._on_type_changed(self._type_combo.currentText())

    def _on_target_changed(self, target: str) -> None:
        for i in range(self._features_list.count()):
            item = self._features_list.item(i)
            if item.text() == target and self._target_combo.isEnabled():
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)

    def _on_add_interaction(self) -> None:
        if not self._session_id:
            return
            
        df = self._data_ctrl.load_dataset(self._session_id)
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        
        from app.ui.dialogs.add_interaction_dialog import AddInteractionDialog
        from PySide6.QtWidgets import QDialog
        
        dlg = AddInteractionDialog(numeric_cols, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            f1, f2 = dlg.get_features()
            if f1 and f2:
                new_col = f"{f1} * {f2}"
                if new_col in df.columns:
                    self._show_error(f"Interaction variable '{new_col}' already exists.")
                    return
                try:
                    df[new_col] = df[f1] * df[f2]
                    # Since we modified the dataset, we should save it using the same mechanism 
                    # as PreprocessingController.
                    self._data_ctrl._blobs.save_dataset(self._session_id, df, original=False)
                    self._data_ctrl._invalidate_cache(self._session_id)
                    
                    # Refresh view
                    self._refresh_columns()
                    
                    # Auto-check the new feature
                    for i in range(self._features_list.count()):
                        item = self._features_list.item(i)
                        if item.text() == new_col:
                            item.setCheckState(Qt.CheckState.Checked)
                            break
                            
                except Exception as e:
                    self._show_error(f"Failed to create interaction variable: {e}")

    def _refresh_models(self) -> None:
        if not self._session_id:
            return
        self._models_list.blockSignals(True)
        self._models_list.clear()
        models = self._model_ctrl.get_models(self._session_id)
        for m in models:
            spec = json.loads(m["spec_json"])
            algo = spec.get("model_type", "unknown")
            item = QListWidgetItem(f"{m['name']} ({algo})")
            item.setData(Qt.ItemDataRole.UserRole, m)
            self._models_list.addItem(item)
        self._models_list.blockSignals(False)
        self._details_lbl.setText("Select a model to view details.")

    def _on_type_changed(self, model_type: str) -> None:
        if model_type == "kmeans":
            self._target_combo.setEnabled(False)
            self._lbl_target.setText("Target Variable: (N/A for KMeans)")
            self._params_stack.setCurrentIndex(2)
        elif "rf" in model_type:
            self._target_combo.setEnabled(True)
            self._lbl_target.setText("Target Variable (Y):")
            self._params_stack.setCurrentIndex(1)
        else:
            self._target_combo.setEnabled(True)
            self._lbl_target.setText("Target Variable (Y):")
            self._params_stack.setCurrentIndex(0)
            
        self._on_target_changed(self._target_combo.currentText())

    def _on_train(self) -> None:
        if not self._session_id:
            return

        name = self._name_edit.text().strip()
        if not name:
            self._show_error("Please provide a name for the model.")
            return

        model_type = self._type_combo.currentText()
        target = self._target_combo.currentText()
        
        if model_type != "kmeans" and not target:
            self._show_error("Please select a target variable.")
            return

        features = []
        for i in range(self._features_list.count()):
            item = self._features_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                features.append(item.text())

        if not features:
            self._show_error("Please select at least one feature.")
            return

        params: dict[str, Any] = {}
        if "rf" in model_type:
            params["n_estimators"] = self._rf_est.value()
        elif model_type == "kmeans":
            params["n_clusters"] = self._km_k.value()

        try:
            self._btn_train.setEnabled(False)
            self._btn_train.setText("Training...")
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            
            artifact = self._model_ctrl.train_and_save_model(
                self._session_id, name, model_type, target if model_type != "kmeans" else None, features, params
            )
            self._refresh_models()
            
            # Select new model
            for i in range(self._models_list.count()):
                item = self._models_list.item(i)
                m = item.data(Qt.ItemDataRole.UserRole)
                if m["id"] == artifact["id"]:
                    self._models_list.setCurrentItem(item)
                    break
                    
        finally:
            self._btn_train.setEnabled(True)
            self._btn_train.setText("Train Model")

    def _on_find_best(self) -> None:
        if not self._session_id:
            return

        name = self._name_edit.text().strip()
        if not name:
            self._show_error("Please provide a name for the model.")
            return

        target = self._target_combo.currentText()
        if not target:
            self._show_error("Please select a target variable.")
            return

        candidates = []
        for i in range(self._features_list.count()):
            item = self._features_list.item(i)
            # Find best considers all checked features as candidates
            if item.checkState() == Qt.CheckState.Checked:
                candidates.append(item.text())

        if len(candidates) < 2:
            self._show_error("Please select at least two candidate features.")
            return

        from PySide6.QtWidgets import QInputDialog
        levels = ["0.01", "0.05", "0.10", "0.20"]
        level_str, ok = QInputDialog.getItem(
            self,
            "Significance Level",
            "Select maximum p-value (alpha) to keep a variable:",
            levels,
            1, # Default index 1 is "0.05"
            False
        )
        if not ok:
            return
            
        alpha = float(level_str)

        try:
            self._btn_best.setEnabled(False)
            self._btn_best.setText("Searching...")
            self._btn_train.setEnabled(False)
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            
            artifact = self._model_ctrl.train_stepwise_ols(
                self._session_id, name, target, candidates, alpha=alpha
            )
            self._refresh_models()
            
            # Select new model
            for i in range(self._models_list.count()):
                item = self._models_list.item(i)
                m = item.data(Qt.ItemDataRole.UserRole)
                if m["id"] == artifact["id"]:
                    self._models_list.setCurrentItem(item)
                    break
                    
        finally:
            self._btn_best.setEnabled(True)
            self._btn_best.setText("Find Best Model")
            self._btn_train.setEnabled(True)

    def _on_delete_model(self) -> None:
        items = self._models_list.selectedItems()
        if not items:
            return
            
        m = items[0].data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the model '{m['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._model_ctrl.delete_model(m["id"])
            self._refresh_models()

    def _on_model_select(self) -> None:
        items = self._models_list.selectedItems()
        if not items:
            self._btn_delete_model.setEnabled(False)
            self._details_lbl.setText("")
            return
            
        self._btn_delete_model.setEnabled(True)
        m = items[0].data(Qt.ItemDataRole.UserRole)
        spec = json.loads(m["spec_json"])
        
        details = [
            f"<b>Name:</b> {m['name']}",
            f"<b>Algorithm:</b> {spec.get('model_type')}",
            f"<b>Target:</b> {spec.get('target', 'N/A')}",
            f"<b>Features ({len(spec.get('features', []))}):</b><br/>" + ", ".join(spec.get('features', [])),
        ]
        
        # Hyperparameters — show "None" when empty (e.g. OLS/Logistic)
        params = spec.get("params", {})
        if params:
            details.append("<br/><b>Hyperparameters:</b>")
            for k, v in params.items():
                details.append(f" - {k}: {v}")
        else:
            details.append("<br/><b>Hyperparameters:</b> None")
            
        details.append("<br/><b>Performance Metrics:</b>")
        metrics = spec.get("metrics", {})
        coef_table = metrics.get("coef_table", None)
        
        for k, v in metrics.items():
            if k == "coef_table":
                continue
            if isinstance(v, float):
                details.append(f" - <b>{k}</b>: {v:.4f}")
            else:
                details.append(f" - <b>{k}</b>: {v}")
        
        # If coef_table is missing (old model), try to extract from the saved model object
        if coef_table is None and spec.get("model_type") == "ols" and self._session_id:
            coef_table = self._extract_coef_table_from_disk(m, spec)
                
        if coef_table:
            # Build equation: Y = b0 + b1*X1 + b2*X2 + ...
            target = spec.get("target", "Y")
            eq_parts = []
            for row in coef_table:
                var = row["variable"]
                coef = row["coef"]
                if var == "const":
                    eq_parts.insert(0, f"{coef}")
                else:
                    sign = "+" if coef >= 0 else "-"
                    eq_parts.append(f"{sign} {abs(coef)}·{var}")
            equation = f"{target} = " + " ".join(eq_parts)
            details.append(f"<br/><b>Equation:</b><br/><code style='font-size: 11px; word-wrap: break-word;'>{equation}</code>")
            
            details.append("<br/><b>Coefficients:</b>")
            details.append(
                "<table style='width:100%; border-collapse: collapse; margin-top: 4px; font-size: 11px;'>"
                "<tr style='background-color: #f0f0f0; border-bottom: 2px solid #c5c5d2;'>"
                "<th style='padding: 3px 4px; text-align: left;'>Variable</th>"
                "<th style='padding: 3px 4px; text-align: right;'>Coef</th>"
                "<th style='padding: 3px 4px; text-align: right;'>Std Err</th>"
                "<th style='padding: 3px 4px; text-align: right;'>t</th>"
                "<th style='padding: 3px 4px; text-align: right;'>P>|t|</th>"
                "<th style='padding: 3px 4px; text-align: center;'>Sig.</th>"
                "<th style='padding: 3px 4px; text-align: right;'>[0.025</th>"
                "<th style='padding: 3px 4px; text-align: right;'>0.975]</th></tr>"
            )
            # Find the non-significant predictor with highest p-value (exclude const)
            worst_var = None
            worst_p = -1.0
            for row in coef_table:
                if row["variable"] != "const" and row["p"] >= 0.05 and row["p"] > worst_p:
                    worst_p = row["p"]
                    worst_var = row["variable"]
            
            for row in coef_table:
                p = row['p']
                if p < 0.001:
                    sig = "***"
                elif p < 0.01:
                    sig = "**"
                elif p < 0.05:
                    sig = "*"
                elif p < 0.1:
                    sig = "."
                else:
                    sig = ""
                
                bg = "background-color: #fce4e4;" if row["variable"] == worst_var else ""
                details.append(
                    f"<tr style='border-bottom: 1px solid #e6e9e8; {bg}'>"
                    f"<td style='padding: 2px 4px;'>{row['variable']}</td>"
                    f"<td style='padding: 2px 4px; text-align: right;'>{row['coef']}</td>"
                    f"<td style='padding: 2px 4px; text-align: right;'>{row['std_err']}</td>"
                    f"<td style='padding: 2px 4px; text-align: right;'>{row['t']}</td>"
                    f"<td style='padding: 2px 4px; text-align: right;'>{p}</td>"
                    f"<td style='padding: 2px 4px; text-align: center;'>{sig}</td>"
                    f"<td style='padding: 2px 4px; text-align: right;'>{row['ci_low']}</td>"
                    f"<td style='padding: 2px 4px; text-align: right;'>{row['ci_high']}</td></tr>"
                )
            details.append("</table>")
            legend = "Signif: *** &lt;0.001, ** &lt;0.01, * &lt;0.05, . &lt;0.1"
            if worst_var:
                legend += f" | <span style='background-color: #fce4e4; padding: 0 4px;'>Highlighted</span>: least significant predictor (candidate for removal)"
            details.append(f"<span style='font-size: 10px; color: #757681;'>{legend}</span>")
                
        self._details_lbl.setText("<br/>".join(details))

    def _extract_coef_table_from_disk(self, artifact: dict, spec: dict) -> list[dict] | None:
        """Load a statsmodels OLS result from joblib and extract coefficients."""
        try:
            blob_path = artifact.get("blob_path", "")
            if not blob_path:
                return None
            # blob_path is like "models/model_xxxx.joblib"
            model_id = blob_path.replace("models/", "").replace(".joblib", "")
            model_obj = self._data_ctrl._blobs.load_model(self._session_id, model_id)
            
            # statsmodels RegressionResultsWrapper
            if not hasattr(model_obj, "params"):
                return None
                
            conf_int = model_obj.conf_int()
            coef_table = []
            for i, var in enumerate(model_obj.params.index):
                coef_table.append({
                    "variable": str(var),
                    "coef": round(float(model_obj.params.iloc[i]), 4),
                    "std_err": round(float(model_obj.bse.iloc[i]), 4),
                    "t": round(float(model_obj.tvalues.iloc[i]), 4),
                    "p": round(float(model_obj.pvalues.iloc[i]), 4),
                    "ci_low": round(float(conf_int.iloc[i, 0]), 4),
                    "ci_high": round(float(conf_int.iloc[i, 1]), 4),
                })
            return coef_table
        except Exception:
            return None

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Modeling Error", message)
