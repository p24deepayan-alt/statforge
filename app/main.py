"""StatForge Entry Point."""

import sys
from pathlib import Path

# Ensure the root project directory is in sys.path so 'import app.xxx' works
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

from app.controllers.data_controller import DataController
from app.controllers.model_controller import ModelController
from app.controllers.plot_controller import PlotController
from app.controllers.preprocessing_controller import PreprocessingController
from app.controllers.session_controller import SessionController
from app.controllers.comparison_controller import ComparisonController
from app.persistence.blob_store import BlobStore
from app.persistence.store import SessionStore
from app.ui.main_window import MainWindow


def main() -> None:
    """Bootstrap and run the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("StatForge")

    # Paths
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "statforge_data"
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / "registry.db"

    # Persistence
    store = SessionStore(db_path)
    blobs = BlobStore(data_dir)

    # Controllers
    session_ctrl = SessionController(store, blobs)
    data_ctrl = DataController(store, blobs)
    prep_ctrl = PreprocessingController(store, blobs, data_ctrl)
    plot_ctrl = PlotController(store, blobs, data_ctrl)
    model_ctrl = ModelController(store, blobs, data_ctrl)
    comp_ctrl = ComparisonController(store, blobs, data_ctrl, model_ctrl)

    # Load theme
    qss_path = base_dir / "resources" / "styles" / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    else:
        print("Warning: theme.qss not found. Using default styles.")

    # UI
    window = MainWindow(session_ctrl, data_ctrl, prep_ctrl, plot_ctrl, model_ctrl, comp_ctrl)
    window.show()

    # Run
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
