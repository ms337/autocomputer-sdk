from pydantic import BaseModel
from typing import Any, Dict, Literal, Optional, Union
from autocomputer_sdk.types.computer import UploadedFileResult, DownloadedFileResult


class UploadedFileResponse(BaseModel):
    """Response after uploading data to a file on a remote computer."""

    result: UploadedFileResult


class DownloadedFileResponse(BaseModel):
    """Response after downloading a file from a remote computer."""

    result: DownloadedFileResult


class ComputerStatusResponse(BaseModel):
    """Response for checking if a computer is running."""

    computer_id: str
    is_running: bool


# ----- Response Message Types -----
class RunStartedMessage(BaseModel):
    """Message indicating a run has started."""

    type: Literal["run_started"] = "run_started"


class RunSequenceStatusMessage(BaseModel):
    """Message for reporting sequence execution status updates."""

    type: Literal["sequence_status"] = "sequence_status"
    sequence_id: str
    success: bool
    error: Optional[str] = None


class RunAssistantMessage(BaseModel):
    """Message containing assistant output."""

    type: Literal["assistant"] = "assistant"
    content: Dict[str, Any]  # ACContentBlock - keeping as Dict for SDK simplicity


class RunErrorMessage(BaseModel):
    """Message indicating an error occurred."""

    type: Literal["error"] = "error"
    error: str


class RunCompletedMessage(BaseModel):
    """Message indicating a run has completed successfully."""

    type: Literal["run_completed"] = "run_completed"


# Union type for all possible message types
RunMessage = Union[
    RunStartedMessage,
    RunSequenceStatusMessage,
    RunAssistantMessage,
    RunErrorMessage,
    RunCompletedMessage,
]
