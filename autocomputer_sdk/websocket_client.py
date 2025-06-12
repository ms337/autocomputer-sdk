"""WebSocket client for local workflow execution."""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp
import httpx
from autocomputer_sdk.types.workflow import Workflow
from autocomputer_sdk.types.messages.response import (
    RunMessage,
    RunStartedMessage,
    RunSequenceStatusMessage,
    RunAssistantMessage,
    RunErrorMessage,
    RunCompletedMessage,
)
from autocomputer_sdk.types.messages.ws import (
    ConfigureMessage,
    StartWorkflowMessage,
    WorkflowContent,
    WSToolResponseMessage,
    ACContentBlock,
)
from autocomputer_sdk.types.computer import Config, ScreenConfig

logger = logging.getLogger(__name__)


class LocalToolServer:
    """Handles communication with local tool server."""
    
    def __init__(self, tool_server_url: str):
        self.tool_server_url = tool_server_url
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def start(self):
        """Initialize connection to tool server."""
        self._session = aiohttp.ClientSession()
        
        # Test connection
        try:
            async with self._session.get(f"{self.tool_server_url}/tools") as response:
                if response.status != 200:
                    raise RuntimeError(f"Tool server not accessible: {response.status}")
                logger.info(f"Connected to tool server at {self.tool_server_url}")
        except Exception as e:
            await self.close()
            raise RuntimeError(f"Failed to connect to tool server: {e}")
    
    async def execute_tool(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool request on the local tool server."""
        if not self._session:
            raise RuntimeError("Tool server not started")
            
        try:
            async with self._session.post(
                f"{self.tool_server_url}/tool/{tool_name}", 
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {"error": f"Tool server error: {response.status} - {error_text}"}
                    
                return await response.json()
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}
    
    async def close(self):
        """Close tool server connection."""
        if self._session:
            await self._session.close()
            self._session = None


class WebSocketWorkflowClient:
    """WebSocket client for workflow execution with tool multiplexing."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.replace("http", "ws").rstrip("/")
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
        
    async def run_workflow(
        self,
        workflow: Workflow,
        user_inputs: Dict[str, Any],
        config: Dict[str, Any],
        tool_server: LocalToolServer
    ) -> AsyncIterator[RunMessage]:
        """Run workflow via WebSocket with tool multiplexing."""
        
        ws_url = f"{self.base_url}/ws/workflow"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.ws_connect(
                    ws_url, 
                    headers=self.headers
                ) as ws:
                    logger.info("WebSocket connected for workflow execution")
                    
                    # Send configuration message using typed class
                    config_obj = Config(**config)
                    config_msg = ConfigureMessage(content=config_obj)
                    await ws.send_str(config_msg.model_dump_json())
                    
                    # Wait for configuration acknowledgment
                    config_ack = await ws.receive()
                    if config_ack.type == aiohttp.WSMsgType.TEXT:
                        ack_data = json.loads(config_ack.data)
                        if ack_data.get("type") != "configure_ack":
                            raise RuntimeError(f"Expected configure_ack, got: {ack_data}")
                    
                    # Send workflow start message using typed class
                    workflow_content = WorkflowContent(
                        workflow=workflow,
                        user_inputs=user_inputs,
                        os_name=config.get("os_name", "linux"),
                        screen=ScreenConfig(**config["screen"])
                    )
                    start_msg = StartWorkflowMessage(content=workflow_content)
                    await ws.send_str(start_msg.model_dump_json())
                    
                    yield RunStartedMessage(type="run_started")
                    
                    # Handle messages
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                message_type = data.get("type")
                                
                                if message_type == "tool_request":
                                    # Handle tool request
                                    await self._handle_tool_request(ws, data, tool_server)
                                    
                                elif message_type == "assistant":
                                    # Forward assistant message
                                    yield RunAssistantMessage(
                                        type="assistant",
                                        content=data["content"]
                                    )
                                    
                                elif message_type == "sequence_status":
                                    yield RunSequenceStatusMessage(
                                        type="sequence_status",
                                        sequence_id=data["sequence_id"],
                                        success=data["success"],
                                        error=data.get("error")
                                    )
                                    
                                elif message_type == "workflow_completed":
                                    yield RunCompletedMessage(type="run_completed")
                                    break
                                    
                                elif message_type == "error":
                                    yield RunErrorMessage(
                                        type="error",
                                        error=data["content"]
                                    )
                                    break
                                    
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to decode WebSocket message: {e}")
                                yield RunErrorMessage(
                                    type="error",
                                    error=f"Failed to decode message: {e}"
                                )
                                
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WebSocket error: {ws.exception()}")
                            yield RunErrorMessage(
                                type="error",
                                error=f"WebSocket error: {ws.exception()}"
                            )
                            break
                            
            except Exception as e:
                logger.error(f"WebSocket workflow execution failed: {e}")
                yield RunErrorMessage(
                    type="error",
                    error=f"WebSocket execution failed: {str(e)}"
                )
    
    async def _handle_tool_request(
        self, 
        ws: aiohttp.ClientWebSocketResponse,
        data: Dict[str, Any],
        tool_server: LocalToolServer
    ):
        """Handle tool request from server."""
        try:
            tool_content = data["content"]
            tool_name = tool_content["tool_name"]
            payload = tool_content["payload"]
            
            logger.info(f"Executing tool: {tool_name}")
            
            # Execute tool locally
            result = await tool_server.execute_tool(tool_name, payload)
            
            # Send response back using typed class
            response_msg = WSToolResponseMessage(content=result)
            await ws.send_str(response_msg.model_dump_json())
            
        except Exception as e:
            logger.error(f"Error handling tool request: {e}")
            # Send error response using typed class
            error_response = WSToolResponseMessage(
                content={"error": f"Tool execution failed: {str(e)}"}
            )
            await ws.send_str(error_response.model_dump_json()) 