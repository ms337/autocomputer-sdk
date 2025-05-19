"""
AutoComputer API Client

A well-structured SDK for AutoComputer Flow API with namespaced routes and strong typing.

Features:
1. Namespaced routes (client.workflows.list(), client.run.astream())
2. Strong typing for request/response objects
3. Async streaming support
"""

import json
from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Optional,
)

import httpx
from autocomputer_sdk.types.computer import (
    RunComputer,
)
from autocomputer_sdk.types.workflow import WorkflowSummary, Workflow
from autocomputer_sdk.types.messages.response import (
    RunMessage,
    RunStartedMessage,
    RunSequenceStatusMessage,
    RunAssistantMessage,
    RunErrorMessage,
    RunCompletedMessage,
)
from autocomputer_sdk.types.messages.request import (
    CreateRunRequest,
)


# ----- Base Namespace Class -----


class BaseNamespace:
    """Base class for all API namespaces."""

    def __init__(self, client: "AutoComputerClient"):
        self.client = client
        self.base_url = client.base_url
        self.headers = client.headers


# ----- Workflows Namespace -----
class WorkflowsNamespace(BaseNamespace):
    """Namespace for workflow-related operations."""

    async def list(self, timeout: Optional[float] = None) -> List[WorkflowSummary]:
        """List all available workflows."""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.get(
                f"{self.base_url}/provision/workflows", headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return [
                WorkflowSummary.model_validate(workflow)
                for workflow in data["workflows"]
            ]

    async def get(
        self, workflow_id: str, timeout: Optional[float] = None
    ) -> Dict[str, Any]:  # Workflow
        """Get a specific workflow by ID."""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.get(
                f"{self.base_url}/provision/workflows/{workflow_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def save(
        self, workflow: Dict[str, Any], user_id: Optional[str] = None
    ) -> WorkflowSummary:
        """Save a workflow."""
        params = {}
        if user_id:
            params["user_id"] = user_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/provision/workflows",
                headers=self.headers,
                json=workflow,
                params=params,
            )
            response.raise_for_status()
            return WorkflowSummary.model_validate(response.json())

    async def delete(self, workflow_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a workflow by ID."""
        params = {}
        if user_id:
            params["user_id"] = user_id

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/provision/workflows/{workflow_id}",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            return True


# ----- Run Namespace -----


class RunNamespace(BaseNamespace):
    """Namespace for workflow execution operations."""

    async def astream(
        self,
        remote_computer: RunComputer,
        workflow: Workflow,
        user_inputs: Dict[str, Any],
    ) -> AsyncIterator[RunMessage]:
        """
        Run a workflow with async streaming responses.

        Args:
            workflow_id: ID of the workflow to run
            user_inputs: Optional inputs for the workflow
            remote_computer: Optional configuration for the remote computer

        Returns:
            AsyncIterator of RunMessage objects
        """

        url = f"{self.base_url}/runs"
        payload = CreateRunRequest(
            remote_computer=remote_computer, workflow=workflow, user_inputs=user_inputs
        ).model_dump()

        async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
            async with client.stream(
                "POST", url, headers=self.headers, json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        message_data = json.loads(line)
                        message_type = message_data.get("type")

                        if message_type == "run_started":
                            yield RunStartedMessage()
                        elif message_type == "sequence_status":
                            yield RunSequenceStatusMessage(
                                sequence_id=message_data["sequence_id"],
                                success=message_data["success"],
                                error=message_data.get("error"),
                            )
                        elif message_type == "assistant":
                            yield RunAssistantMessage(content=message_data["content"])
                        elif message_type == "error":
                            yield RunErrorMessage(error=message_data["error"])
                        elif message_type == "run_completed":
                            yield RunCompletedMessage()
                    except json.JSONDecodeError:
                        yield RunErrorMessage(error=f"Failed to decode message: {line}")


# ----- Main Client Class -----


class AutoComputerClient:
    """AutoComputer client for interacting with the Flow API.

    Access API functionality through namespaced routes:
    - client.workflows.list() - List all workflows
    - client.workflows.get(id) - Get a workflow by ID
    - client.run.astream() - Run a workflow with streaming responses
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the Flow API client.

        Args:
            base_url: The base URL of the Flow API (e.g., http://localhost:8765)
            api_key: Your API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }

        # Initialize namespaces
        self.workflows = WorkflowsNamespace(self)
        self.run = RunNamespace(self)
