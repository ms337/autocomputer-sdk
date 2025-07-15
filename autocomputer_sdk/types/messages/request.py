from typing import Any, Dict

from pydantic import BaseModel

from autocomputer_sdk.types.computer import RunningComputer
from autocomputer_sdk.types.workflow import Workflow


class CreateRunRequest(BaseModel):
    remote_computer: RunningComputer
    workflow: Workflow
    user_inputs: Dict[str, Any]


class UploadDataToFileRequest(BaseModel):
    """Request to upload data to a file on a remote computer."""

    file_path: str
    contents: str

class DownloadFileRequest(BaseModel):
    remote_path: str
    max_size_bytes: int = 100 * 1024 * 1024  # 100MB for both files and archives
    is_dir: bool = False  # True to download as directory archive
