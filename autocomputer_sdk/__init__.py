"""AutoComputer SDK for Flow API."""

from .client import AutoComputerClient
from .types.vm import VMStatus, VMInstance, VMConfig
from .vm_manager import LocalVMManager

# WebSocket message types
from .types.messages.ws import (
    ConfigureMessage,
    StartWorkflowMessage,
    WorkflowContent,
    AssistantMessage,
    ErrorMessage,
    WSToolRequestMessage,
    WSToolResponseMessage,
    ACContentBlock,
    ACTextBlock,
    ACThinkingBlock,
    ACToolUseBlock,
    ACToolUseResultBlock,
)

__all__ = [
    # Main client and VM management
    "AutoComputerClient",
    "VMStatus", 
    "VMInstance",
    "VMConfig",
    "LocalVMManager",
    
    # WebSocket message types
    "ConfigureMessage",
    "StartWorkflowMessage", 
    "WorkflowContent",
    "AssistantMessage",
    "ErrorMessage",
    "WSToolRequestMessage",
    "WSToolResponseMessage",
    "ACContentBlock",
    "ACTextBlock",
    "ACThinkingBlock", 
    "ACToolUseBlock",
    "ACToolUseResultBlock",
]

__version__ = "1.0.0" 