from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, field_validator

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


class Provider(str, Enum):
    E2B = "e2b"
    RDP = "rdp"


class WinRMSettings(BaseModel):
    endpoint: Optional[str] = None
    port: int = 5986
    use_ssl: bool = True
    username: Optional[str] = None
    password_secret_id: Optional[str] = None


class E2BMetadata(BaseModel):
    tool_server_url: str
    vnc_url: str
    vnc_auth_key: Optional[str] = None
    vnc_view_only: bool = False


class SSHMetadata(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    available: bool = False


class RDPGateway(BaseModel):
    """Base gateway configuration for RDP connections."""
    host: str
    port: int = 443
    username: Optional[str] = None
    domain: Optional[str] = None


class RDPGatewayCredentials(RDPGateway):
    """Gateway configuration with credentials for starting RDP connections.
    
    Extends RDPGateway to include password field for authentication.
    """
    password: Optional[str] = None


# Backwards compatibility aliases
RDPGatewayMetadata = RDPGateway  # Deprecated: Use RDPGateway instead
RDPGatewaySettings = RDPGatewayCredentials  # Deprecated: Use RDPGatewayCredentials instead


class StartRDPComputerRequest(BaseModel):
    """Request payload for starting an RDP computer."""
    host: str
    port: int = 3389
    username: str
    password: str
    domain: Optional[str] = None
    gateway: Optional[RDPGatewayCredentials] = None


class RDPMetadata(BaseModel):
    host: str
    port: int = 3389
    username: str
    domain: Optional[str] = None
    display_width: int
    display_height: int
    guacd_tunnel_id: Optional[str] = None
    credential_secret_id: Optional[str] = None
    winrm: Optional[WinRMSettings] = None
    ssh: Optional[SSHMetadata] = None
    gateway: Optional[RDPGateway] = None  # Response data doesn't include password


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
    provider: Provider = Provider.E2B
    tool_server_url: Optional[str] = None
    vnc_url: Optional[str] = None
    vnc_auth_key: Optional[str] = None
    vnc_view_only: bool = False
    e2b: Optional[E2BMetadata] = None
    rdp: Optional[RDPMetadata] = None

    # throw error if tool_server_url has trailing slash
    @field_validator("tool_server_url", mode="before")
    def remove_trailing_slash(cls, v):
        if v is None:
            return v
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
    contents: str  # Base64 encoded content (files or archives)
    is_dir: bool = False


class ComputerStatusResponse(BaseModel):
    """Response for checking if a computer is running."""

    computer_id: str
    is_running: bool