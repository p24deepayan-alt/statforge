import tempfile
from pathlib import Path
import pandas as pd
import pytest
from app.persistence.store import SessionStore
from app.persistence.blob_store import BlobStore
from app.controllers.data_controller import DataController
from app.controllers.preprocessing_controller import PreprocessingController
from app.controllers.model_controller import ModelController

@pytest.fixture
def temp_env():
    with tempfile.TemporaryDirectory() as d:
        d_path = Path(d)
        store = SessionStore(d_path / "test.db")
        blobs = BlobStore(d_path)
        data_ctrl = DataController(store, blobs)
        prep_ctrl = PreprocessingController(store, blobs, data_ctrl)
        model_ctrl = ModelController(store, blobs, data_ctrl)
        yield d_path, store, blobs, data_ctrl, prep_ctrl, model_ctrl

def test_full_workflow(temp_env):
    d_path, store, blobs, data_ctrl, prep_ctrl, model_ctrl = temp_env
    
    # 1. Create Session
    session = store.create_session("Integration Test")
    sid = session["id"]
    
    # 2. Import Data (simulated by direct save)
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "Target": [0, 1, 0]})
    blobs.save_dataset(sid, df, original=True)
    blobs.save_dataset(sid, df, original=False)
    
    # 3. Train Model
    artifact = model_ctrl.train_and_save_model(
        sid, "Logistic Model", "logistic", "Target", ["A", "B"], {}
    )
    
    assert artifact["kind"] == "model"
    
    # 4. Check outputs
    models = model_ctrl.get_models(sid)
    assert len(models) == 1
    assert models[0]["name"] == "Logistic Model"
