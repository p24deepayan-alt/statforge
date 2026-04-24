import tempfile
from pathlib import Path
import pandas as pd
import pytest
from app.persistence.store import SessionStore
from app.persistence.blob_store import BlobStore

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

def test_session_store(temp_dir):
    db_path = temp_dir / "test.db"
    store = SessionStore(db_path)
    
    # Create
    session = store.create_session("Test Session")
    assert session["name"] == "Test Session"
    assert session["id"] is not None
    
    # List
    sessions = store.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session["id"]
    
    # Update
    store.update_session(session["id"], row_count=100)
    updated = store.get_session(session["id"])
    assert updated["row_count"] == 100
    
    # Delete
    store.delete_session(session["id"])
    assert store.get_session(session["id"]) is None

def test_blob_store(temp_dir):
    blobs = BlobStore(temp_dir)
    session_id = "test_session_123"
    
    df = pd.DataFrame({"A": [1, 2, 3]})
    
    # Save
    blobs.save_dataset(session_id, df)
    assert blobs.dataset_exists(session_id)
    
    # Load
    loaded_df = blobs.load_dataset(session_id)
    assert len(loaded_df) == 3
    
    # Delete
    blobs.delete_session_blobs(session_id)
    assert not blobs.dataset_exists(session_id)
