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
    ListedRunningComputer,
    GetRunningComputer,
    DeletedComputer,
    RunningComputer,
)
from autocomputer_sdk.types.workflow import WorkflowSummary, Workflow
from autocomputer_sdk.types.messages.response import (
    RunMessage,
    RunStartedMessage,
    RunSequenceStatusMessage,
    RunAssistantMessage,
    RunErrorMessage,
    RunCompletedMessage,
    UploadedFileResponse,
    DownloadedFileResponse,
    ComputerStatusResponse,
)
from autocomputer_sdk.types.messages.request import (
    CreateRunRequest,
    UploadDataToFileRequest,
    DownloadFileRequest,
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
                f"{self.base_url}/workflows", headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return [
                WorkflowSummary.model_validate(workflow)
                for workflow in data["workflows"]
            ]

    async def get(
        self, workflow_id: str, timeout: Optional[float] = None
    ) -> Workflow:  # Workflow
        """Get a specific workflow by ID."""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.get(
                f"{self.base_url}/workflows/{workflow_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            return Workflow.model_validate(response.json())

    async def save(
        self, workflow: Dict[str, Any], user_id: Optional[str] = None
    ) -> WorkflowSummary:
        """Save a workflow."""
        params = {}
        if user_id:
            params["user_id"] = user_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/workflows",
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
                f"{self.base_url}/workflows/{workflow_id}",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            return True


# ----- Computers Namespace -----


class ComputerNamespace(BaseNamespace):
    """Namespace for remote computer operations."""

    async def list(
        self, timeout: Optional[float] = None
    ) -> List[ListedRunningComputer]:
        """List all available remote computers for the user."""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.get(
                f"{self.base_url}/computers/", headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return [
                ListedRunningComputer.model_validate(computer)
                for computer in data["computers"]
            ]

    async def get(
        self, computer_id: str, timeout: Optional[float] = None
    ) -> GetRunningComputer:
        """Get detailed information about a running computer by ID."""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.get(
                f"{self.base_url}/computers/{computer_id}/",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            return GetRunningComputer.model_validate(data)

    async def start(
        self,
        config: Dict[str, Any],
        template_id: Optional[str] = None,
        sandbox_id: Optional[str] = None,
        vnc_requires_auth: bool = False,
        vnc_view_only: bool = False,
        timeout: Optional[float] = None,
    ) -> RunningComputer:
        """Start a new remote computer with the given configuration.

        Args:
            config: Configuration for the remote computer
            template_id: Optional template ID to use for the computer
            vnc_requires_auth: Whether VNC requires authentication
            vnc_view_only: Whether VNC is view-only
            timeout: Optional timeout for the HTTP request

        Returns:
            A RunningComputer instance with connection details
        """
        payload = {
            "config": config,
            "vnc_requires_auth": vnc_requires_auth,
            "vnc_view_only": vnc_view_only,
        }

        if template_id:
            payload["template_id"] = template_id

        if sandbox_id:
            payload["sandbox_id"] = sandbox_id

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.post(
                f"{self.base_url}/computers/",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return RunningComputer.model_validate(data["computer"])

    async def delete(
        self, computer_id: str, timeout: Optional[float] = None
    ) -> DeletedComputer:
        """Delete a remote computer by ID."""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.delete(
                f"{self.base_url}/computers/{computer_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            # Response for delete returns a DeleteResponse with message and computer_id
            data = response.json()
            return DeletedComputer.model_validate(data)

    async def upload_data_to_file(
        self,
        computer_id: str,
        file_path: str,
        contents: str,
        timeout: Optional[float] = None,
    ) -> UploadedFileResponse:
        """Upload data to a file on a remote computer.

        Args:
            computer_id: The ID of the computer to upload the data to
            file_path: The path where the file should be created/written
            contents: The data to upload as a string
            timeout: Optional timeout for the HTTP request

        Returns:
            UploadedFileResponse containing the result of the upload operation
        """
        payload = UploadDataToFileRequest(file_path=file_path, contents=contents)

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.post(
                f"{self.base_url}/computers/{computer_id}/upload",
                headers=self.headers,
                json=payload.model_dump(),
            )
            response.raise_for_status()
            data = response.json()
            return UploadedFileResponse.model_validate(data)

    async def download_file(
        self,
        computer_id: str,
        remote_path: str,
        max_size_bytes: int = 10 * 1024 * 1024,
        timeout: Optional[float] = None,
    ) -> DownloadedFileResponse:
        """Download a file from a remote computer."""

        payload = DownloadFileRequest(
            remote_path=remote_path,
            max_size_bytes=max_size_bytes,
        )

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.post(
                f"{self.base_url}/computers/{computer_id}/download",
                headers=self.headers,
                json=payload.model_dump(),
            )
            response.raise_for_status()
            data = response.json()
            return DownloadedFileResponse.model_validate(data)

    async def is_running(
        self, computer_id: str, timeout: Optional[float] = None
    ) -> ComputerStatusResponse:
        """Check if a remote computer is running.

        Args:
            computer_id: The ID of the computer to check
            timeout: Optional timeout for the HTTP request

        Returns:
            ComputerIsRunningResponse with computer_id and is_running status
        """
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.get(
                f"{self.base_url}/computers/{computer_id}/status",
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            return ComputerStatusResponse.model_validate(data)


# ----- Run Namespace -----


class RunNamespace(BaseNamespace):
    """Namespace for workflow execution operations."""

    async def astream(
        self,
        remote_computer: RunningComputer,
        workflow: Workflow,
        user_inputs: Dict[str, Any],
        timeout: Optional[float] = None,
    ) -> AsyncIterator[RunMessage]:
        """
        Run a workflow with async streaming responses.

        Args:
            remote_computer: The RunComputer instance to execute the workflow on
            workflow: The Workflow object containing the workflow definition
            user_inputs: User inputs for the workflow execution
            timeout: Optional timeout for the initial HTTP connection (streaming has no timeout)

        Returns:
            AsyncIterator of RunMessage objects representing the streaming response
        """

        url = f"{self.base_url}/runs"
        payload = CreateRunRequest(
            remote_computer=remote_computer, workflow=workflow, user_inputs=user_inputs
        ).model_dump()

        # Use None timeout for streaming connection to prevent timeouts during long-running workflows
        async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
            async with client.stream(
                "POST", url, headers=self.headers, json=payload
            ) as response:
                response.raise_for_status()
                _ = response.headers.get("X-Session-ID")

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        message_data = json.loads(line)
                        message_type = message_data.get("type")

                        if message_type == "run_started":
                            yield RunStartedMessage(type="run_started")
                        elif message_type == "sequence_status":
                            yield RunSequenceStatusMessage(
                                type="sequence_status",
                                sequence_id=message_data["sequence_id"],
                                success=message_data["success"],
                                error=message_data.get("error"),
                            )
                        elif message_type == "assistant":
                            yield RunAssistantMessage(
                                type="assistant", content=message_data["content"]
                            )
                        elif message_type == "error":
                            yield RunErrorMessage(
                                type="error", error=message_data["error"]
                            )
                        elif message_type == "run_completed":
                            yield RunCompletedMessage(type="run_completed")
                    except json.JSONDecodeError:
                        yield RunErrorMessage(
                            type="error", error=f"Failed to decode message: {line}"
                        )


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
        self.computer = ComputerNamespace(self)
