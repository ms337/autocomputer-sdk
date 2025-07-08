"""VM-related types for local execution."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class VMStatus(BaseModel):
    """Status of a VirtualBox VM."""
    name: str
    state: Literal["running", "stopped", "paused", "suspended", "unknown"]
    ip_address: Optional[str] = None
    tool_server_accessible: bool = False


class VMInstance(BaseModel):
    """Instance of a running VM."""
    name: str
    computer_id: str
    ip_address: Optional[str] = None
    tool_server_url: str
    screen_width: int
    screen_height: int
    started_at: datetime
    config: dict  # The Config object passed to start_vm


class VMConfig(BaseModel):
    """Configuration for local VM execution."""
    screen_width: int = 1920
    screen_height: int = 1080
    display_num: int = 0
    tool_server_url: str = "http://localhost:3333"
