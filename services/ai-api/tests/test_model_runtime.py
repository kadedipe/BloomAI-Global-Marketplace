from pathlib import Path

from app.model_runtime import ModelRuntime


def test_sha256(tmp_path: Path):
    artifact = tmp_path / "artifact.pth"
    artifact.write_bytes(b"bloomai")
    assert ModelRuntime.sha256(artifact) == "b94fb87d6b15844a831f5c1c807a96764c4a5cffa45fe25e9a205b7d0fdf0cc4"


def test_unconfigured_runtime_is_not_ready(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "missing.pth"))
    monkeypatch.delenv("MODEL_GDRIVE_FILE_ID", raising=False)
    model_runtime = ModelRuntime()
    model_runtime.initialize()
    assert not model_runtime.ready
    assert "MODEL_GDRIVE_FILE_ID" in model_runtime.status()["error"]
