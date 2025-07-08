"""Local execution namespaces for AutoComputer SDK."""

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

from autocomputer_sdk.types.computer import Config
from autocomputer_sdk.types.messages.response import RunMessage
from autocomputer_sdk.types.vm import VMInstance, VMStatus
from autocomputer_sdk.types.workflow import Workflow
from autocomputer_sdk.websocket_client import LocalToolServer, WebSocketWorkflowClient

logger = logging.getLogger(__name__)


class VMNamespace:
    """Namespace for VM lifecycle management."""

    def __init__(self, client: "AutoComputerClient", vm_manager=None):
        self.client = client
        self.base_url = client.base_url
        self.headers = client.headers
        self.vm_manager = vm_manager  # Dependency injected LocalVMManager
        self._running_vms: Dict[str, VMInstance] = {}

    def set_vm_manager(self, vm_manager):
        """Set the VM manager (for dependency injection)."""
        self.vm_manager = vm_manager

    async def start_vbox(
        self,
        vm_name: Optional[str] = None,
        screen_width: int = 1920,
        screen_height: int = 1080,
        headless: bool = True,
        wait_for_tool_server: bool = True,
        tool_server_port: int = 3333,
        timeout: int = 120
    ) -> VMInstance:
        """Start a VirtualBox VM and wait for tool server to be ready.

        Args:
            vm_name: Name of VirtualBox VM (auto-detect if None)
            screen_width: VM screen width
            screen_height: VM screen height
            headless: Run in headless mode
            wait_for_tool_server: Wait for tool server to be accessible
            tool_server_port: Port where tool server runs
            timeout: Max seconds to wait for VM startup

        Returns:
            VMInstance with connection details
        """
        if not self.vm_manager:
            raise RuntimeError("VM manager not initialized. Please set a LocalVMManager instance.")

        if vm_name is None:
            # Auto-detect VM name - for now just require it
            raise ValueError("vm_name is required")

        logger.info(f"Starting VirtualBox VM: {vm_name}")

        # Create config for the VM
        config = Config(
            screen={
                "width": screen_width,
                "height": screen_height,
                "display_num": 0
            }
        )

        try:
            # Start VM using the manager
            running_computer = self.vm_manager.start_vm(
                vm_name=vm_name,
                config=config,
                tool_server_port=tool_server_port
            )

            # Wait for tool server if requested
            if wait_for_tool_server:
                await self._wait_for_tool_server(
                    running_computer.tool_server_url,
                    timeout
                )

            # Create VM instance config with os_name explicitly included
            instance_config = config.model_dump()
            instance_config["os_name"] = "linux"  # Ensure os_name is explicitly set

            # Create VM instance
            vm_instance = VMInstance(
                name=vm_name,
                computer_id=running_computer.computer_id,
                ip_address=self.vm_manager.get_vm_ip(vm_name),
                tool_server_url=running_computer.tool_server_url,
                screen_width=screen_width,
                screen_height=screen_height,
                started_at=datetime.now(),
                config=instance_config
            )

            # Store the running VM
            self._running_vms[vm_name] = vm_instance

            logger.info(f"VM started successfully: {vm_name}")
            return vm_instance

        except Exception as e:
            logger.error(f"Failed to start VM {vm_name}: {e}")
            raise RuntimeError(f"Failed to start VM {vm_name}: {str(e)}")

    async def _wait_for_tool_server(self, tool_server_url: str, timeout: int):
        """Wait for tool server to become accessible."""
        import aiohttp

        logger.info(f"Waiting for tool server at {tool_server_url}")
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{tool_server_url}/tools", timeout=5) as response:
                        if response.status == 200:
                            logger.info("Tool server is accessible")
                            return
            except Exception:
                pass  # Continue waiting

            await asyncio.sleep(2)

        raise RuntimeError(f"Tool server not accessible after {timeout} seconds")

    async def stop_vbox(self, vm_name: Optional[str] = None) -> bool:
        """Stop the VirtualBox VM."""
        if not self.vm_manager:
            raise RuntimeError("VM manager not initialized")

        if vm_name is None:
            raise ValueError("vm_name is required")

        try:
            logger.info(f"Stopping VM: {vm_name}")
            self.vm_manager.stop_vm(vm_name)

            # Remove from running VMs
            if vm_name in self._running_vms:
                del self._running_vms[vm_name]

            logger.info(f"VM stopped successfully: {vm_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop VM {vm_name}: {e}")
            return False

    async def list_vms(self) -> List[str]:
        """List available VirtualBox VMs."""
        if not self.vm_manager:
            raise RuntimeError("VM manager not initialized")

        # This would need to be implemented in LocalVMManager
        # For now, return running VMs
        return list(self._running_vms.keys())

    async def get_status(self, vm_name: Optional[str] = None) -> VMStatus:
        """Get current VM status (running, stopped, etc.)."""
        if not self.vm_manager:
            raise RuntimeError("VM manager not initialized")

        if vm_name is None:
            raise ValueError("vm_name is required")

        try:
            is_running = self.vm_manager.is_vm_running(vm_name)
            ip_address = self.vm_manager.get_vm_ip(vm_name) if is_running else None

            # Check tool server accessibility
            tool_server_accessible = False
            if is_running and vm_name in self._running_vms:
                try:
                    import aiohttp
                    vm_instance = self._running_vms[vm_name]
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{vm_instance.tool_server_url}/tools", timeout=5) as response:
                            tool_server_accessible = response.status == 200
                except Exception:
                    pass

            return VMStatus(
                name=vm_name,
                state="running" if is_running else "stopped",
                ip_address=ip_address,
                tool_server_accessible=tool_server_accessible
            )

        except Exception as e:
            logger.error(f"Failed to get VM status for {vm_name}: {e}")
            return VMStatus(
                name=vm_name,
                state="unknown",
                ip_address=None,
                tool_server_accessible=False
            )


class LocalNamespace:
    """Namespace for local VM execution operations."""

    def __init__(self, client: "AutoComputerClient", vm_manager=None):
        self.client = client
        self.base_url = client.base_url
        self.headers = client.headers
        self.vm = VMNamespace(client, vm_manager)

    def set_vm_manager(self, vm_manager):
        """Set the VM manager for both this namespace and the VM namespace."""
        self.vm.set_vm_manager(vm_manager)

    async def connect_and_run_workflow(
        self,
        workflow: Workflow,
        user_inputs: Dict[str, Any],
        vm_instance: Optional[VMInstance] = None,
        tool_server_url: str = "http://localhost:3333",
        screen_width: int = 1920,
        screen_height: int = 1080,
        display_num: int = 0
    ) -> AsyncIterator[RunMessage]:
        """Connect to VM and run workflow via WebSocket.

        Args:
            workflow: Workflow to execute
            user_inputs: User inputs for workflow
            vm_instance: VM instance from start_vbox() (optional)
            tool_server_url: URL of local tool server
            screen_width: Screen width for tools
            screen_height: Screen height for tools
            display_num: Display number

        Returns:
            AsyncIterator of RunMessage objects
        """

        # Use VM instance config if provided, otherwise use parameters
        if vm_instance:
            actual_tool_server_url = vm_instance.tool_server_url
            actual_screen_width = vm_instance.screen_width
            actual_screen_height = vm_instance.screen_height
            config_dict = vm_instance.config
            # Ensure os_name is present in the config
            if "os_name" not in config_dict:
                config_dict["os_name"] = "linux"  # Default to linux for local VMs
        else:
            actual_tool_server_url = tool_server_url
            actual_screen_width = screen_width
            actual_screen_height = screen_height
            config_dict = {
                "screen": {
                    "width": actual_screen_width,
                    "height": actual_screen_height,
                    "display_num": display_num
                },
                "os_name": "linux"  # Default to linux for local VMs
            }

        # Initialize tool server
        tool_server = LocalToolServer(actual_tool_server_url)

        try:
            await tool_server.start()
            logger.info(f"Connected to tool server at {actual_tool_server_url}")

            # Initialize WebSocket client
            ws_client = WebSocketWorkflowClient(self.base_url, self.client.api_key)

            # Run workflow
            async for message in ws_client.run_workflow(
                workflow=workflow,
                user_inputs=user_inputs,
                config=config_dict,
                tool_server=tool_server
            ):
                yield message

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            from autocomputer_sdk.types.messages.response import RunErrorMessage
            yield RunErrorMessage(type="error", error=str(e))

        finally:
            # Clean up tool server connection
            await tool_server.close()
            logger.info("Tool server connection closed")
