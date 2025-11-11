"""
AutoComputer API Client

A well-structured SDK for AutoComputer Flow API with namespaced routes and strong typing.

Features:
1. Namespaced routes (client.workflows.list(), client.run.astream())
2. Strong typing for request/response objects
3. Async streaming support
4. Local VM execution via WebSocket
"""

import base64
import json
from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Optional,
    Union,
)

import httpx

from autocomputer_sdk.local_namespaces import LocalNamespace
from autocomputer_sdk.types.computer import (
    ComputerStatusResponse,
    Config,
    DeletedComputer,
    DownloadedFileResult,
    GetRunningComputer,
    ListedRunningComputer,
    Provider,
    RDPGatewayCredentials,
    RunningComputer,
    StartRDPComputerRequest,
    UploadedFileResult,
)
from autocomputer_sdk.types.messages.request import (
    CreateRunRequest,
    DownloadFileRequest,
    UploadDataToFileRequest,
)
from autocomputer_sdk.types.messages.response import (
    DownloadedFileResponse,
    RunAssistantMessage,
    RunCompletedMessage,
    RunErrorMessage,
    RunMessage,
    RunSequenceStartedMessage,
    RunSequenceStatusMessage,
    RunStartedMessage,
    UploadedFileResponse,
)
from autocomputer_sdk.types.workflow import Workflow, WorkflowSummary

# ----- Base Namespace Class -----


class BaseNamespace:
    """Base class for all API namespaces."""

    def __init__(self, client: "AutoComputerClient"):
        self.client = client
        self.base_url = client.base_url
        self.headers = client.headers

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> Optional[str]:
        content_type = response.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            try:
                payload = response.json()
            except ValueError:
                pass
            else:
                detail = payload.get("detail")
                if isinstance(detail, str):
                    detail = detail.strip()
                    if detail:
                        return detail
                elif detail is not None:
                    return str(detail)

        text = response.text.strip()
        if text:
            trimmed = text if len(text) <= 500 else f"{text[:497]}..."
            return trimmed
        return None

    def _raise_for_status(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = self._extract_error_detail(response)
            if detail:
                message = f"{response.status_code} {response.reason_phrase}: {detail}"
                raise httpx.HTTPStatusError(
                    message,
                    request=exc.request,
                    response=exc.response,
                ) from None
            raise


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
            self._raise_for_status(response)
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
            self._raise_for_status(response)
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
            self._raise_for_status(response)
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
            self._raise_for_status(response)
            return True


# ----- Computers Namespace -----


class ComputerNamespace(BaseNamespace):
    """Namespace for remote computer operations."""

    async def list(
        self,
        timeout: Optional[float] = None,
        provider: Provider = Provider.E2B,
    ) -> List[ListedRunningComputer]:
        """List all available remote computers for the user."""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.get(
                f"{self.base_url}/computers/",
                headers=self.headers,
                params={"provider": provider.value},
            )
            self._raise_for_status(response)
            data = response.json()
            return [
                ListedRunningComputer.model_validate(computer)
                for computer in data["computers"]
            ]

    async def get(
        self,
        computer_id: str,
        timeout: Optional[float] = None,
        provider: Provider = Provider.E2B,
    ) -> GetRunningComputer:
        """Get detailed information about a running computer by ID."""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.get(
                f"{self.base_url}/computers/{computer_id}/",
                headers=self.headers,
                params={"provider": provider.value},
            )
            self._raise_for_status(response)
            data = response.json()
            return GetRunningComputer.model_validate(data)

    async def start(
        self,
        config: Union[Config, Dict[str, Any]],
        template_id: Optional[str] = None,
        sandbox_id: Optional[str] = None,
        vnc_requires_auth: bool = False,
        vnc_view_only: bool = False,
        provider: Provider = Provider.E2B,
        rdp: Optional[Union[StartRDPComputerRequest, Dict[str, Any]]] = None,
        timeout: Optional[float] = None,
    ) -> RunningComputer:
        """Start a new remote computer with the given configuration.

        Args:
            config: Configuration for the remote computer (Config object or dict)
            template_id: Optional template ID to use for the computer
            sandbox_id: Optional sandbox ID to use for the computer (E2B only)
            vnc_requires_auth: Whether VNC requires authentication
            vnc_view_only: Whether VNC is view-only
            provider: Provider to use (E2B or RDP)
            rdp: RDP configuration (StartRDPComputerRequest object or dict, required if provider=RDP)
            timeout: Optional timeout for the HTTP request

        Returns:
            A RunningComputer instance with connection details
        """
        # Convert typed objects to dicts if needed
        if isinstance(config, Config):
            config = config.model_dump()
        
        if isinstance(rdp, StartRDPComputerRequest):
            rdp = rdp.model_dump(exclude_none=True)
        
        payload: Dict[str, Any] = {
            "config": config,
            "provider": provider.value,
            "vnc_requires_auth": vnc_requires_auth,
            "vnc_view_only": vnc_view_only,
        }

        if provider == Provider.E2B:
            if template_id:
                payload["template_id"] = template_id
            if sandbox_id:
                payload["sandbox_id"] = sandbox_id
        elif provider == Provider.RDP:
            if rdp is None:
                raise ValueError("rdp configuration is required when provider='rdp'")
            payload["rdp"] = rdp
        else:
            raise ValueError(f"Unsupported provider {provider}")

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.post(
                f"{self.base_url}/computers/",
                headers=self.headers,
                json=payload,
            )
            self._raise_for_status(response)
            data = response.json()
            return RunningComputer.model_validate(data["computer"])

    async def delete(
        self,
        computer_id: str,
        timeout: Optional[float] = None,
        provider: Provider = Provider.E2B,
    ) -> DeletedComputer:
        """Delete a remote computer by ID."""
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.delete(
                f"{self.base_url}/computers/{computer_id}",
                headers=self.headers,
                params={"provider": provider.value},
            )
            self._raise_for_status(response)
            # Response for delete returns a DeleteResponse with message and computer_id
            data = response.json()
            return DeletedComputer.model_validate(data)

    async def upload_data_to_file(
        self,
        computer_id: str,
        file_path: str,
        contents: str,
        timeout: Optional[float] = None,
        provider: Provider = Provider.E2B,
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
                params={"provider": provider.value},
                json=payload.model_dump(),
            )
            self._raise_for_status(response)
            data = response.json()
            return UploadedFileResponse.model_validate(data)

    async def download_file(
        self,
        computer_id: str,
        remote_path: str,
        max_size_bytes: int = 100 * 1024 * 1024,
        is_dir: bool = False,
        timeout: Optional[float] = None,
        provider: Provider = Provider.E2B,
    ) -> DownloadedFileResponse:
        """Download a file or directory from a remote computer.
        
        Args:
            computer_id: The ID of the computer to download from
            remote_path: The path to the file or directory
            max_size_bytes: Maximum allowed size (default: 100MB)
            is_dir: True to download as directory archive, False for single file
            timeout: Optional timeout for the HTTP request
            
        Returns:
            DownloadedFileResponse with base64 encoded content
            
        Note:
            - All content is returned as base64 encoded bytes
            - Use save_downloaded_content() helper to save to local files
        """

        payload = DownloadFileRequest(
            remote_path=remote_path,
            max_size_bytes=max_size_bytes,
            is_dir=is_dir,
        )

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = await client.post(
                f"{self.base_url}/computers/{computer_id}/download",
                headers=self.headers,
                params={"provider": provider.value},
                json=payload.model_dump(),
            )
            self._raise_for_status(response)
            data = response.json()
            return DownloadedFileResponse.model_validate(data)

    def save_downloaded_content(
        self,
        download_response: DownloadedFileResponse, 
        local_path: str
    ) -> bool:
        """
        Save downloaded content to a local file.
        
        Args:
            download_response: The response from download_file()
            local_path: Local path where to save the content
            
        Returns:
            True if saved successfully, False otherwise
            
        Note:
            - All content is base64 encoded and saved as binary
            - For directories, use .tar.gz extension
            - For files, use appropriate extension for the file type
        """
        try:
            result = download_response.result
            
            # Decode base64 and save as binary
            content_bytes = base64.b64decode(result.contents)
            with open(local_path, 'wb') as f:
                f.write(content_bytes)
                
            return True
        except Exception:
            return False

    async def is_running(
        self,
        computer_id: str,
        timeout: Optional[float] = None,
        provider: Provider = Provider.E2B,
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
                params={"provider": provider.value},
            )
            self._raise_for_status(response)
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
                self._raise_for_status(response)
                _ = response.headers.get("X-Session-ID")

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        message_data = json.loads(line)
                        message_type = message_data.get("type")

                        if message_type == "run_started":
                            yield RunStartedMessage(type="run_started")
                        elif message_type == "sequence_started":
                            yield RunSequenceStartedMessage(
                                type="sequence_started",
                                sequence_id=message_data["sequence_id"]
                            )
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
    - client.local.vm.start_vbox() - Start a local VirtualBox VM
    - client.local.connect_and_run_workflow() - Run workflow on local VM
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
        self.local = LocalNamespace(self)  # New local namespace

    def set_local_vm_manager(self, vm_manager):
        """Set the VM manager for local execution.

        Args:
            vm_manager: Instance of LocalVMManager for managing VirtualBox VMs

        Example:
            from autocomputer_sdk.vm_manager import LocalVMManager

            client = AutoComputerClient(base_url="...", api_key="...")
            vm_manager = LocalVMManager()
            client.set_local_vm_manager(vm_manager)
        """
        self.local.set_vm_manager(vm_manager)

    def cleanup(self):
        """Clean up any resources (like VM manager tunnels)."""
        if hasattr(self.local.vm, 'vm_manager') and self.local.vm.vm_manager:
            if hasattr(self.local.vm.vm_manager, 'cleanup'):
                self.local.vm.vm_manager.cleanup()