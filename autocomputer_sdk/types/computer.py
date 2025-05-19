from pydantic import BaseModel, validator

# ----- Type Definitions -----


class ScreenConfig(BaseModel):
    """Screen configuration for a remote computer."""

    width: int = 1440
    height: int = 900
    display_num: int = 0


class Config(BaseModel):
    """Configuration for a remote computer."""

    screen: ScreenConfig
    os_name: str


class RunComputer(BaseModel):
    """Remote computer configuration."""

    config: Config
    tool_server_url: str

    # throw error if tool_server_url has trailing slash
    @validator("tool_server_url", pre=True)
    def remove_trailing_slash(cls, v):
        if v.endswith("/"):
            raise ValueError("tool_server_url must not have trailing slash")
        return v
