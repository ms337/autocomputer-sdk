from typing import Any, Dict, Literal, Union

from pydantic import BaseModel

# ===== Assistant Content Blocks =====

class ACTextBlock(BaseModel):
    """Text content block."""
    type: Literal["text"] = "text"
    text: str


class ACThinkingBlock(BaseModel):
    """Thinking content block."""
    type: Literal["thinking"] = "thinking"
    thinking: str


class ACToolUseBlock(BaseModel):
    """Tool use content block."""
    type: Literal["tool_use"] = "tool_use"
    name: str
    input: Dict[str, Any]


class ACToolUseResultBlock(BaseModel):
    """Tool use result content block."""
    type: Literal["tool_use_result"] = "tool_use_result"
    result: Dict[str, Any]  # ToolResult serialized


# Union type for all content blocks
ACContentBlock = Union[ACTextBlock, ACThinkingBlock, ACToolUseBlock, ACToolUseResultBlock]
