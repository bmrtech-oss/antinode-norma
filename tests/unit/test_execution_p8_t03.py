from pathlib import Path
from antinode_norma.execution.artifacts import ArtifactManager, ArtifactType


def test_artifact_manager_save_and_get(tmp_path):
    manager = ArtifactManager(output_dir=tmp_path)
    data = b"\x89PNG\r\n\x1a\nfake_image_bytes"

    art = manager.save_artifact(
        execution_id="EXEC-1",
        artifact_type=ArtifactType.SCREENSHOT,
        source_data=data,
        filename="failure.png",
        content_type="image/png",
    )

    assert art.execution_id == "EXEC-1"
    assert art.artifact_type == ArtifactType.SCREENSHOT
    assert art.size_bytes == len(data)
    assert Path(art.file_path).exists()

    retrieved = manager.get_artifacts(execution_id="EXEC-1", artifact_type=ArtifactType.SCREENSHOT)
    assert len(retrieved) == 1
    assert retrieved[0].id == art.id


def test_artifact_manager_clear(tmp_path):
    manager = ArtifactManager(output_dir=tmp_path)
    manager.save_artifact("EXEC-1", ArtifactType.LOG, b"log data 1", "test1.log")
    manager.save_artifact("EXEC-2", ArtifactType.LOG, b"log data 2", "test2.log")

    assert len(manager.get_artifacts()) == 2

    # Clear EXEC-1
    manager.clear_artifacts(execution_id="EXEC-1")
    assert len(manager.get_artifacts()) == 1
    assert manager.get_artifacts()[0].execution_id == "EXEC-2"

    # Clear all
    manager.clear_artifacts()
    assert len(manager.get_artifacts()) == 0
