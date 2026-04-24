"""Main application window — handles sidebar navigation and active workspace swapping."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QFrame,
    QDialog,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.controllers.data_controller import DataController
from app.controllers.plot_controller import PlotController
from app.controllers.preprocessing_controller import PreprocessingController
from app.controllers.session_controller import SessionController
from app.controllers.model_controller import ModelController
from app.controllers.comparison_controller import ComparisonController
from app.ui.data_view import DataView
from app.ui.dialogs.new_session_dialog import NewSessionDialog
from app.ui.graphs_view import GraphsView
from app.ui.import_preview import ImportPreviewDialog
from app.ui.modeling_view import ModelingView
from app.ui.model_comparison import ModelComparisonView
from app.ui.preprocessing_view import PreprocessingView
from app.ui.report_builder import ReportBuilderView
from app.ui.sessions_home import SessionsHome
from app.util import strings


class MainWindow(QMainWindow):
    """The main shell of StatForge. Contains the sidebar and a stack of workspaces."""

    def __init__(self, session_ctrl: SessionController, data_ctrl: DataController, prep_ctrl: PreprocessingController, plot_ctrl: PlotController, model_ctrl: ModelController, comp_ctrl: ComparisonController):
        super().__init__()
        self._session_ctrl = session_ctrl
        self._data_ctrl = data_ctrl
        self._prep_ctrl = prep_ctrl
        self._plot_ctrl = plot_ctrl
        self._model_ctrl = model_ctrl
        self._comp_ctrl = comp_ctrl

        self.setWindowTitle(strings.APP_NAME)
        self.setMinimumSize(1280, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_lyt = QVBoxLayout(sidebar)
        sidebar_lyt.setContentsMargins(0, 0, 0, 0)
        sidebar_lyt.setSpacing(0)

        brand_name = QLabel(strings.APP_NAME)
        brand_name.setObjectName("brand_name")
        brand_sub = QLabel(strings.APP_SUBTITLE)
        brand_sub.setObjectName("brand_subtitle")
        sidebar_lyt.addWidget(brand_name)
        sidebar_lyt.addWidget(brand_sub)
        sidebar_lyt.addSpacing(16)

        # Nav Buttons
        self._nav_buttons: dict[QWidget, QPushButton] = {}

        def add_nav(label: str, target: QWidget | None = None) -> QPushButton:
            btn = QPushButton(label)
            btn.setProperty("class", "nav_button")
            if target:
                btn.clicked.connect(lambda: self._switch_view(target))
                self._nav_buttons[target] = btn
            sidebar_lyt.addWidget(btn)
            return btn

        # The different views
        self._home_view = SessionsHome(self._session_ctrl)
        self._data_view = DataView(self._data_ctrl)
        self._prep_view = PreprocessingView(self._data_ctrl, self._prep_ctrl)
        self._graphs_view = GraphsView(self._data_ctrl, self._plot_ctrl)
        self._modeling_view = ModelingView(self._data_ctrl, self._model_ctrl)
        self._model_comp_view = ModelComparisonView(self._model_ctrl, self._comp_ctrl)
        self._report_view = ReportBuilderView(self._session_ctrl, self._plot_ctrl, self._model_ctrl)
        
        # Connect signals
        self._home_view._btn_new.clicked.connect(self._on_new_session)
        self._home_view.session_opened.connect(self._on_open_session)
        self._prep_ctrl.pipeline_changed.connect(self._on_pipeline_changed)
        self._plot_ctrl.plot_created.connect(self._on_artifact_created)
        self._model_ctrl.model_trained.connect(self._on_artifact_created)
        self._comp_ctrl.comparison_created.connect(self._on_artifact_created)

        add_nav(strings.NAV_SESSIONS, self._home_view)
        sidebar_lyt.addSpacing(16)
        
        # Disabled views until session is loaded
        self._nav_data = add_nav(strings.NAV_DATA_VIEW, self._data_view)
        self._nav_pre = add_nav(strings.NAV_PREPROCESSING, self._prep_view)
        self._nav_graphs = add_nav(strings.NAV_GRAPHS, self._graphs_view)
        self._nav_models = add_nav(strings.NAV_MODELING, self._modeling_view)
        self._nav_comp = add_nav(strings.NAV_COMPARISON, self._model_comp_view)
        self._nav_report = add_nav(strings.NAV_REPORT_BUILDER, self._report_view)
        
        sidebar_lyt.addStretch()
        
        # Footer
        add_nav(strings.NAV_DOCUMENTATION)
        add_nav(strings.NAV_SUPPORT)
        sidebar_lyt.addSpacing(16)

        main_layout.addWidget(sidebar)

        # ── Main Stack ───────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.addWidget(self._home_view)
        self._stack.addWidget(self._data_view)
        self._stack.addWidget(self._prep_view)
        self._stack.addWidget(self._graphs_view)
        self._stack.addWidget(self._modeling_view)
        self._stack.addWidget(self._model_comp_view)
        self._stack.addWidget(self._report_view)
        main_layout.addWidget(self._stack, 1)

        self._set_session_nav_enabled(False)
        self._switch_view(self._home_view)

    # ── Nav ──────────────────────────────────────────────────

    def _switch_view(self, view: QWidget) -> None:
        self._stack.setCurrentWidget(view)
        for target, btn in self._nav_buttons.items():
            btn.setProperty("active", str(target == view).lower())
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _set_session_nav_enabled(self, enabled: bool) -> None:
        self._nav_data.setEnabled(enabled)
        self._nav_pre.setEnabled(enabled)
        self._nav_graphs.setEnabled(enabled)
        self._nav_models.setEnabled(enabled)
        self._nav_comp.setEnabled(enabled)
        self._nav_report.setEnabled(enabled)

    # ── Session lifecycle ────────────────────────────────────

    def _on_new_session(self) -> None:
        dlg = NewSessionDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
            
        name = dlg.session_name()
        file_path = dlg.file_path()
        
        if not name:
            name = "Untitled Session"
            
        if not file_path:
            # We allow empty sessions to be created.
            session = self._session_ctrl.create_session(name)
            self._on_open_session(session["id"])
            return
            
        # Preview the file
        preview_dlg = ImportPreviewDialog(file_path, self._data_ctrl, self)
        if preview_dlg.exec() != QDialog.DialogCode.Accepted:
            return
            
        # Do the import
        config = preview_dlg.get_import_config()
        session = self._session_ctrl.create_session(name)
        
        # Run import blocking for now
        self._data_ctrl.import_file(
            session_id=session["id"],
            path=file_path,
            delimiter=config["delimiter"],
            has_header=config["has_header"],
            encoding=config["encoding"],
        )
        
        self._on_open_session(session["id"])

    def _on_open_session(self, session_id: str) -> None:
        self._session_ctrl.open_session(session_id)
        if self._data_ctrl.has_dataset(session_id):
            self._data_view.load_session(session_id)
            self._prep_view.load_session(session_id)
            self._graphs_view.load_session(session_id)
            self._modeling_view.load_session(session_id)
            self._model_comp_view.load_session(session_id)
            self._report_view.load_session(session_id)
            self._set_session_nav_enabled(True)
            self._switch_view(self._data_view)
        else:
            self._set_session_nav_enabled(True)
            self._nav_data.setEnabled(False) # No data yet
            self._nav_pre.setEnabled(False)
            self._nav_graphs.setEnabled(False)
            self._nav_models.setEnabled(False)
            self._nav_comp.setEnabled(False)
            self._nav_report.setEnabled(False)
            # For now, just stay on home.

    def _on_pipeline_changed(self, session_id: str) -> None:
        # Re-load data in views
        if self._data_ctrl.has_dataset(session_id):
            self._data_view.load_session(session_id)
            self._graphs_view.load_session(session_id)
            self._modeling_view.load_session(session_id)

    def _on_artifact_created(self, artifact_id: str) -> None:
        session_id = self._session_ctrl.active_session_id
        if session_id:
            self._model_comp_view.load_session(session_id)
            self._report_view.load_session(session_id)
