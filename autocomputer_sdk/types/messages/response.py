from typing import Literal, Optional, Union

from pydantic import BaseModel

from autocomputer_sdk.types.computer import DownloadedFileResult, UploadedFileResult
from autocomputer_sdk.types.messages.content_blocks import ACContentBlock


class UploadedFileResponse(BaseModel):
    """Response after uploading data to a file on a remote computer."""

    result: UploadedFileResult


class DownloadedFileResponse(BaseModel):
    """Response after downloading a file from a remote computer."""

    result: DownloadedFileResult


# ----- Response Message Types -----
class RunStartedMessage(BaseModel):
    """Message indicating a run has started."""

    type: Literal["run_started"] = "run_started"


class RunSequenceStartedMessage(BaseModel):
    """Message indicating a sequence has started."""

    type: Literal["sequence_started"] = "sequence_started"
    sequence_id: str


class RunSequenceStatusMessage(BaseModel):
    """Message for reporting sequence execution status updates."""

    type: Literal["sequence_status"] = "sequence_status"
    sequence_id: str
    success: bool
    error: Optional[str] = None


class RunAssistantMessage(BaseModel):
    """Message containing assistant output."""

    type: Literal["assistant"] = "assistant"
    content: ACContentBlock


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
    RunSequenceStartedMessage,
    RunSequenceStatusMessage,
    RunAssistantMessage,
    RunErrorMessage,
    RunCompletedMessage,
]
