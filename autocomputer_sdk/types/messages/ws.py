"""WebSocket message types for AutoComputer Flow API communication."""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel

from autocomputer_sdk.types.computer import Config, ScreenConfig
from autocomputer_sdk.types.workflow import Workflow


# ===== Base Message Types =====

class BaseMessage(BaseModel):
    """Base class for all WebSocket messages."""
    type: str
    correlation_id: Optional[str] = None
    version: str = "1.0"


# ===== Configuration Messages =====

class ConfigureMessage(BaseMessage):
    """Message to configure the WebSocket connection."""
    type: Literal["configure"] = "configure"
    content: Config


class ConfigurationAckMessage(BaseMessage):
    """Acknowledgment of configuration."""
    type: Literal["configure_ack"] = "configure_ack"
    content: str


# ===== Workflow Content and Messages =====

class WorkflowContent(BaseModel):
    """Content for starting a workflow."""
    workflow: Workflow
    user_inputs: Dict[str, Any]
    os_name: str
    screen: ScreenConfig


class StartWorkflowMessage(BaseMessage):
    """Message to start a workflow."""
    type: Literal["start_workflow"] = "start_workflow"
    content: WorkflowContent


class WorkflowCompletedMessage(BaseMessage):
    """Message indicating workflow completion."""
    type: Literal["workflow_completed"] = "workflow_completed"
    content: str


class WorkflowSequenceStatusMessage(BaseMessage):
    """Message for workflow sequence status updates."""
    type: Literal["workflow_sequence_status"] = "workflow_sequence_status"
    sequence_id: str
    success: bool
    error: Optional[str] = None


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


class AssistantMessage(BaseMessage):
    """Message containing assistant content."""
    type: Literal["assistant"] = "assistant"
    content: ACContentBlock


# ===== Tool Messages =====

class WSToolRequestContent(BaseModel):
    """Content for tool requests."""
    tool_name: str
    payload: Dict[str, Any]


class WSToolRequestMessage(BaseMessage):
    """Message requesting tool execution."""
    type: Literal["tool_request"] = "tool_request"
    content: WSToolRequestContent


class WSToolResponseMessage(BaseMessage):
    """Message responding to tool request."""
    type: Literal["tool_response"] = "tool_response"
    content: Dict[str, Any]


# ===== Error Messages =====

class ErrorMessage(BaseMessage):
    """Error message."""
    type: Literal["error"] = "error"
    content: str


# ===== Direct Client Messages (for wait_for_human tool) =====

class DirectClientRequestMessage(BaseMessage):
    """Direct client request message."""
    type: Literal["direct_client_request"] = "direct_client_request"
    content: Dict[str, Any]


class DirectClientResponseMessage(BaseMessage):
    """Direct client response message."""
    type: Literal["direct_client_response"] = "direct_client_response"
    content: Dict[str, Any]


class DirectClientResponseError(BaseMessage):
    """Direct client response error."""
    type: Literal["direct_client_response_error"] = "direct_client_response_error"
    error: str


# ===== Message Unions =====

# Messages that the client sends to server
ClientMessage = Union[
    ConfigureMessage,
    StartWorkflowMessage,
    WSToolResponseMessage,
    DirectClientResponseMessage,
    DirectClientResponseError,
]

# Messages that the server sends to client
ServerMessage = Union[
    ConfigurationAckMessage,
    AssistantMessage,
    WorkflowCompletedMessage,
    WorkflowSequenceStatusMessage,
    WSToolRequestMessage,
    ErrorMessage,
    DirectClientRequestMessage,
]

# All possible WebSocket messages
WebSocketMessage = Union[ClientMessage, ServerMessage]
