from autocomputer_sdk.types.computer import RunningComputer
from autocomputer_sdk.types.workflow import Workflow
from pydantic import BaseModel
from typing import Dict, Any


class CreateRunRequest(BaseModel):
    remote_computer: RunningComputer
    workflow: Workflow
    user_inputs: Dict[str, Any]


class UploadDataToFileRequest(BaseModel):
    """Request to upload data to a file on a remote computer."""
    file_path: str
    contents: str