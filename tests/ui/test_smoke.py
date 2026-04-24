import pytest
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

# We need a fixture to provide the QApplication instance for Qt tests
# pytest-qt usually provides `qtbot`, but we can write a simple test

def test_main_window_init(qtbot, mocker):
    # Mock controllers
    session_ctrl = mocker.Mock()
    data_ctrl = mocker.Mock()
    prep_ctrl = mocker.Mock()
    plot_ctrl = mocker.Mock()
    model_ctrl = mocker.Mock()
    comp_ctrl = mocker.Mock()
    
    window = MainWindow(session_ctrl, data_ctrl, prep_ctrl, plot_ctrl, model_ctrl, comp_ctrl)
    qtbot.addWidget(window)
    
    assert window.windowTitle() == "StatForge"
