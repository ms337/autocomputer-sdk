from enum import Enum
from pydantic import BaseModel, field_validator
from typing import List, Optional

# ----- Type Definitions -----


class ScreenConfig(BaseModel):
    """Screen configuration for a remote computer."""

    width: int = 1440
    height: int = 900
    display_num: int = 0


class OSName(str, Enum):
    """Operating system names supported by the platform."""

    DARWIN = "darwin"
    WIN32 = "win32"
    LINUX = "linux"


class Config(BaseModel):
    """Configuration for a remote computer."""

    screen: ScreenConfig
    os_name: OSName = OSName.LINUX
    preferred_browser: Optional[str] = None
    installed_apps: Optional[List[str]] = None


class ListedRunningComputer(BaseModel):
    computer_id: str


class GetRunningComputer(BaseModel):
    computer_id: str
    template_id: Optional[str] = None
    name: Optional[str] = None
    metadata: Optional[dict] = None
    started_at: Optional[str] = None
    end_at: Optional[str] = None


class DeletedComputer(BaseModel):
    message: str
    computer_id: str


class RunningComputer(BaseModel):
    computer_id: str
    config: Config
    tool_server_url: str
    vnc_url: str
    vnc_auth_key: Optional[str] = None
    vnc_view_only: bool = False

    # throw error if tool_server_url has trailing slash
    @field_validator("tool_server_url", mode="before")
    def remove_trailing_slash(cls, v):
        if v.endswith("/"):
            raise ValueError("tool_server_url must not have trailing slash")
        return v


class UploadedFileResult(BaseModel):
    """Result of uploading data to a file on a remote computer."""

    computer_id: str
    file_path: str


class DownloadedFileResult(BaseModel):
    computer_id: str
    file_path: str
    contents: str
