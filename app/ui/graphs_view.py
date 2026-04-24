"""Graphs & Visualisation view."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.controllers.data_controller import DataController
from app.controllers.plot_controller import PlotController
from app.util import strings


class GraphsView(QWidget):
    """UI for building and viewing Seaborn plots."""

    def __init__(
        self, data_ctrl: DataController, plot_ctrl: PlotController, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._data_ctrl = data_ctrl
        self._plot_ctrl = plot_ctrl
        self._session_id: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ── Left: Plot Builder ───────────────────────────────
        left_panel = QFrame()
        left_panel.setProperty("class", "card")
        left_panel.setFixedWidth(300)
        left_lyt = QVBoxLayout(left_panel)
        left_lyt.setSpacing(16)

        title = QLabel("Create Plot")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #191c1c;")
        left_lyt.addWidget(title)

        # Name
        left_lyt.addWidget(QLabel("Plot Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Sales by Region")
        left_lyt.addWidget(self._name_edit)

        # Type
        left_lyt.addWidget(QLabel("Plot Type:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems([
            "histogram", "boxplot", "scatter", "bar", "heatmap", "pairplot"
        ])
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        left_lyt.addWidget(self._type_combo)

        # X Axis
        self._lbl_x = QLabel("X Axis:")
        left_lyt.addWidget(self._lbl_x)
        self._x_combo = QComboBox()
        left_lyt.addWidget(self._x_combo)

        # Y Axis
        self._lbl_y = QLabel("Y Axis:")
        left_lyt.addWidget(self._lbl_y)
        self._y_combo = QComboBox()
        left_lyt.addWidget(self._y_combo)

        # Hue
        self._lbl_hue = QLabel("Grouping (Hue):")
        left_lyt.addWidget(self._lbl_hue)
        self._hue_combo = QComboBox()
        left_lyt.addWidget(self._hue_combo)

        left_lyt.addStretch()

        self._btn_generate = QPushButton("Generate Plot")
        self._btn_generate.setProperty("class", "primary")
        self._btn_generate.clicked.connect(self._on_generate)
        left_lyt.addWidget(self._btn_generate)

        layout.addWidget(left_panel)

        # ── Center: Preview ──────────────────────────────────
        center_panel = QVBoxLayout()
        self._preview_lbl = QLabel("Generate or select a plot from the gallery.")
        self._preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_lbl.setStyleSheet("background: #ffffff; border: 1px solid #c5c5d2; border-radius: 4px;")
        center_panel.addWidget(self._preview_lbl, 1)
        layout.addLayout(center_panel, stretch=1)

        # ── Right: Gallery ───────────────────────────────────
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        
        gal_title = QLabel("Plot Gallery")
        gal_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #191c1c;")
        right_panel.addWidget(gal_title)

        self._gallery_list = QListWidget()
        self._gallery_list.setFixedWidth(200)
        self._gallery_list.setStyleSheet(
            "QListWidget { background: #ffffff; border: 1px solid #c5c5d2; border-radius: 4px; padding: 4px; }"
            "QListWidget::item { padding: 8px; border-bottom: 1px solid #e6e9e8; }"
            "QListWidget::item:selected { background: #dce1ff; color: #001857; }"
        )
        self._gallery_list.itemSelectionChanged.connect(self._on_gallery_select)
        right_panel.addWidget(self._gallery_list)
        
        self._btn_add_report = QPushButton("Add to Report")
        self._btn_add_report.setProperty("class", "secondary")
        self._btn_add_report.setEnabled(False)
        right_panel.addWidget(self._btn_add_report)

        layout.addLayout(right_panel)

        self._plot_ctrl.error_occurred.connect(self._show_error)

    # ── Logic ────────────────────────────────────────────────

    def load_session(self, session_id: str) -> None:
        self._session_id = session_id
        self._refresh_columns()
        self._refresh_gallery()
        self._preview_lbl.setText("Generate or select a plot from the gallery.")

    def _refresh_columns(self) -> None:
        if not self._session_id:
            return
        df = self._data_ctrl.load_dataset(self._session_id)
        cols = [""] + list(df.columns)
        
        # Save state
        x_curr = self._x_combo.currentText()
        y_curr = self._y_combo.currentText()
        hue_curr = self._hue_combo.currentText()

        for cb in (self._x_combo, self._y_combo, self._hue_combo):
            cb.blockSignals(True)
            cb.clear()
            cb.addItems(cols)
            cb.blockSignals(False)

        # Restore state
        def restore(cb: QComboBox, text: str) -> None:
            idx = cb.findText(text)
            if idx >= 0:
                cb.setCurrentIndex(idx)
        restore(self._x_combo, x_curr)
        restore(self._y_combo, y_curr)
        restore(self._hue_combo, hue_curr)

        self._on_type_changed(self._type_combo.currentText())

    def _refresh_gallery(self) -> None:
        if not self._session_id:
            return
        self._gallery_list.blockSignals(True)
        self._gallery_list.clear()
        plots = self._plot_ctrl.get_plots(self._session_id)
        for p in plots:
            # We store the ID in the item's data
            item = QListWidget().item(0) # dummy
            self._gallery_list.addItem(p["name"])
            list_item = self._gallery_list.item(self._gallery_list.count() - 1)
            list_item.setData(Qt.ItemDataRole.UserRole, p["id"])
        self._gallery_list.blockSignals(False)
        self._btn_add_report.setEnabled(False)

    def _on_type_changed(self, plot_type: str) -> None:
        # Enable/disable controls based on plot type
        needs_x = plot_type in ("histogram", "boxplot", "scatter", "bar")
        needs_y = plot_type in ("boxplot", "scatter", "bar")
        needs_hue = plot_type in ("histogram", "boxplot", "scatter", "bar", "pairplot")
        
        self._x_combo.setEnabled(needs_x)
        self._y_combo.setEnabled(needs_y)
        self._hue_combo.setEnabled(needs_hue)
        
        if plot_type == "heatmap":
            self._lbl_x.setText("Variables:")
            self._x_combo.setToolTip("Heatmap uses all numeric variables automatically.")
        elif plot_type == "pairplot":
            self._lbl_x.setText("Variables:")
            self._x_combo.setToolTip("Pairplot uses all numeric variables by default.")
        else:
            self._lbl_x.setText("X Axis:")
            self._x_combo.setToolTip("")

    def _on_generate(self) -> None:
        if not self._session_id:
            return

        name = self._name_edit.text().strip()
        if not name:
            self._show_error("Please provide a name for the plot.")
            return

        plot_type = self._type_combo.currentText()
        x = self._x_combo.currentText()
        y = self._y_combo.currentText()
        hue = self._hue_combo.currentText()

        params: dict[str, Any] = {}
        if self._x_combo.isEnabled() and x: params["x"] = x
        if self._y_combo.isEnabled() and y: params["y"] = y
        if self._hue_combo.isEnabled() and hue: params["hue"] = hue

        if plot_type in ("scatter", "bar") and (not x or not y):
            self._show_error(f"{plot_type.capitalize()} requires both X and Y variables.")
            return

        try:
            self._btn_generate.setEnabled(False)
            self._preview_lbl.setText("Generating...")
            
            # Application needs to process events so UI updates "Generating..."
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            
            artifact = self._plot_ctrl.create_plot(self._session_id, name, plot_type, params)
            self._refresh_gallery()
            
            # Select the newly created plot
            for i in range(self._gallery_list.count()):
                item = self._gallery_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == artifact["id"]:
                    self._gallery_list.setCurrentItem(item)
                    break
                    
        finally:
            self._btn_generate.setEnabled(True)

    def _on_gallery_select(self) -> None:
        items = self._gallery_list.selectedItems()
        if not items:
            self._btn_add_report.setEnabled(False)
            return
            
        self._btn_add_report.setEnabled(True)
        artifact_id = items[0].data(Qt.ItemDataRole.UserRole)
        
        if self._session_id:
            path = self._plot_ctrl.get_plot_image_path(self._session_id, artifact_id)
            if path:
                pixmap = QPixmap(path)
                # Scale to fit preview area while keeping aspect ratio
                scaled = pixmap.scaled(
                    self._preview_lbl.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._preview_lbl.setPixmap(scaled)
            else:
                self._preview_lbl.setText("Image not found.")

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Plot Error", message)
