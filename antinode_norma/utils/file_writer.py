import os
from ..core.schemas import WriteFeatureOutput


def write_feature_file(file_path: str, content: str) -> WriteFeatureOutput:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)
    return WriteFeatureOutput(
        path=file_path, bytes_written=len(content.encode("utf-8"))
    )
