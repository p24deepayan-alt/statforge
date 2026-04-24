"""Report Builder View."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.analysis.reporting import export_html, export_pdf
from app.controllers.model_controller import ModelController
from app.controllers.plot_controller import PlotController
from app.controllers.session_controller import SessionController


class ReportBuilderView(QWidget):
    """UI for assembling artifacts into a final PDF/HTML report."""

    def __init__(
        self,
        session_ctrl: SessionController,
        plot_ctrl: PlotController,
        model_ctrl: ModelController,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._session_ctrl = session_ctrl
        self._plot_ctrl = plot_ctrl
        self._model_ctrl = model_ctrl
        self._session_id: str | None = None
        self._all_artifacts: list[dict[str, Any]] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ── Left: Available Artifacts ────────────────────────
        left_panel = QVBoxLayout()
        left_title = QLabel("Available Artifacts")
        left_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #191c1c;")
        left_panel.addWidget(left_title)

        self._available_list = QListWidget()
        self._available_list.setStyleSheet(
            "QListWidget { background: #ffffff; border: 1px solid #c5c5d2; border-radius: 4px; padding: 4px; }"
            "QListWidget::item { padding: 8px; border-bottom: 1px solid #e6e9e8; }"
            "QListWidget::item:selected { background: #dce1ff; color: #001857; }"
        )
        self._available_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        left_panel.addWidget(self._available_list)
        
        layout.addLayout(left_panel, 1)

        # ── Center: Transfer Buttons ─────────────────────────
        center_panel = QVBoxLayout()
        center_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._btn_add = QPushButton("Add >>")
        self._btn_add.setProperty("class", "secondary")
        self._btn_add.clicked.connect(self._on_add)
        center_panel.addWidget(self._btn_add)
        
        self._btn_remove = QPushButton("<< Remove")
        self._btn_remove.setProperty("class", "secondary")
        self._btn_remove.clicked.connect(self._on_remove)
        center_panel.addWidget(self._btn_remove)
        
        layout.addLayout(center_panel)

        # ── Right: Report Layout ─────────────────────────────
        right_panel = QVBoxLayout()
        right_title = QLabel("Report Layout")
        right_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #191c1c;")
        right_panel.addWidget(right_title)

        self._layout_list = QListWidget()
        self._layout_list.setStyleSheet(
            "QListWidget { background: #ffffff; border: 1px solid #c5c5d2; border-radius: 4px; padding: 4px; }"
            "QListWidget::item { padding: 8px; border-bottom: 1px solid #e6e9e8; }"
            "QListWidget::item:selected { background: #dce1ff; color: #001857; }"
        )
        self._layout_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._layout_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        right_panel.addWidget(self._layout_list, 1)
        
        # Add narrative block & divider
        narrative_lyt = QHBoxLayout()
        
        btn_add_narrative = QPushButton("Add Text Block")
        btn_add_narrative.setProperty("class", "secondary")
        btn_add_narrative.clicked.connect(self._on_add_narrative)
        narrative_lyt.addWidget(btn_add_narrative)
        
        btn_add_divider = QPushButton("Add Divider")
        btn_add_divider.setProperty("class", "secondary")
        btn_add_divider.clicked.connect(self._on_add_divider)
        narrative_lyt.addWidget(btn_add_divider)
        
        narrative_lyt.addStretch()
        right_panel.addLayout(narrative_lyt)

        # Export Buttons
        export_lyt = QHBoxLayout()
        export_lyt.addStretch()
        
        self._btn_export_html = QPushButton("Export HTML")
        self._btn_export_html.setProperty("class", "secondary")
        self._btn_export_html.clicked.connect(self._on_export_html)
        export_lyt.addWidget(self._btn_export_html)
        
        self._btn_export_pdf = QPushButton("Export PDF")
        self._btn_export_pdf.setProperty("class", "primary")
        self._btn_export_pdf.clicked.connect(self._on_export_pdf)
        export_lyt.addWidget(self._btn_export_pdf)
        
        right_panel.addLayout(export_lyt)
        
        layout.addLayout(right_panel, 1)

    def load_session(self, session_id: str) -> None:
        self._session_id = session_id
        self._refresh_available()
        self._layout_list.clear()

    def _refresh_available(self) -> None:
        if not self._session_id:
            return
            
        self._available_list.clear()
        
        plots = self._plot_ctrl.get_plots(self._session_id)
        models = self._model_ctrl.get_models(self._session_id)
        
        self._all_artifacts = plots + models
        
        for a in self._all_artifacts:
            icon = "📊" if a["kind"] == "plot" else "🤖"
            item = QListWidgetItem(f"{icon} {a['name']}")
            # Store the dict for easy building of the layout
            item.setData(Qt.ItemDataRole.UserRole, {"type": "artifact", "artifact_id": a["id"], "obj": a})
            self._available_list.addItem(item)

    def _on_add(self) -> None:
        for item in self._available_list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole)
            new_item = QListWidgetItem(item.text())
            new_item.setData(Qt.ItemDataRole.UserRole, data)
            self._layout_list.addItem(new_item)

    def _on_remove(self) -> None:
        for item in self._layout_list.selectedItems():
            row = self._layout_list.row(item)
            self._layout_list.takeItem(row)

    def _on_add_narrative(self) -> None:
        from app.ui.dialogs.add_text_block_dialog import AddTextBlockDialog
        from PySide6.QtWidgets import QDialog
        
        dlg = AddTextBlockDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            html = dlg.get_html()
            plain_text = dlg.get_plain_text()
            if not plain_text.strip():
                return
                
            item = QListWidgetItem(f"📝 Text: {plain_text[:30]}...")
            item.setData(Qt.ItemDataRole.UserRole, {"type": "narrative", "html": html})
            self._layout_list.addItem(item)
            
    def _on_add_divider(self) -> None:
        from app.ui.dialogs.add_divider_dialog import AddDividerDialog
        from PySide6.QtWidgets import QDialog
        
        dlg = AddDividerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            style = dlg.get_style()
            item = QListWidgetItem(f"➖ Divider: {style}")
            item.setData(Qt.ItemDataRole.UserRole, {"type": "divider", "style": style})
            self._layout_list.addItem(item)

    def _build_layout(self) -> list[dict[str, Any]]:
        layout = []
        for i in range(self._layout_list.count()):
            data = self._layout_list.item(i).data(Qt.ItemDataRole.UserRole)
            # Make sure we don't accidentally pass the full artifact obj to the renderer
            # as it might not serialize, but actually the layout only needs artifact_id
            l_item = {"type": data["type"]}
            if data["type"] == "artifact":
                l_item["artifact_id"] = data["artifact_id"]
            elif data["type"] == "narrative":
                l_item["html"] = data["html"]
            elif data["type"] == "divider":
                l_item["style"] = data["style"]
            layout.append(l_item)
        return layout

    def _on_export_html(self) -> None:
        self._export("html", "HTML Files (*.html)")

    def _on_export_pdf(self) -> None:
        self._export("pdf", "PDF Files (*.pdf)")

    def _export(self, fmt: str, filter_str: str) -> None:
        if not self._session_id or self._layout_list.count() == 0:
            QMessageBox.warning(self, "Empty Report", "Please add items to the report layout.")
            return

        session = self._session_ctrl._store.get_session(self._session_id)
        if not session:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Export {fmt.upper()}", f"{session['name']}_report.{fmt}", filter_str
        )
        
        if not file_path:
            return

        try:
            out_path = Path(file_path)
            layout = self._build_layout()
            blobs_root = self._session_ctrl._blobs.session_dir(self._session_id)
            
            if fmt == "html":
                export_html(self._all_artifacts, layout, session["name"], blobs_root, out_path)
            else:
                export_pdf(self._all_artifacts, layout, session["name"], blobs_root, out_path)
                
            QMessageBox.information(self, "Export Successful", f"Report saved to {out_path.name}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred:\n{str(e)}")
