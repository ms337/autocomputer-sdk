"""
Local VirtualBox VM management for AutoComputer SDK.

This module handles starting, stopping, and managing local VirtualBox VMs
on the client side.
"""

import subprocess
import time
import uuid
from typing import Optional

from autocomputer_sdk.types.computer import (
    Config,
    RunningComputer,
)


class TunnelManager:
    """Placeholder tunnel manager - implement as needed for your use case."""

    def create_tunnel(self, port: int, tunnel_name: str) -> str:
        """Create a tunnel and return the tunneled URL."""
        # This is a placeholder - implement actual tunneling logic
        print(f"Creating tunnel for port {port} with name {tunnel_name}")
        return f"http://localhost:{port}"

    def stop_tunnel(self, tunnel_name: str) -> None:
        """Stop a tunnel."""
        print(f"Stopping tunnel: {tunnel_name}")

    def cleanup(self) -> None:
        """Clean up all tunnels."""
        print("Cleaning up all tunnels")


class LocalVMManager:
    """Manager for local VirtualBox VMs."""

    def __init__(
        self,
        default_tool_server_url: str = "http://localhost:3333",
        default_vnc_url: str = "http://localhost:6080/vnc.html",
        default_vnc_requires_auth: bool = False,
        default_vnc_view_only: bool = False,
        enable_tunneling: bool = True
    ):
        """Initialize the Local VM manager."""
        self._check_virtualbox_installation()
        self.default_tool_server_url = default_tool_server_url
        self.default_vnc_url = default_vnc_url
        self.default_vnc_requires_auth = default_vnc_requires_auth
        self.default_vnc_view_only = default_vnc_view_only
        self.enable_tunneling = enable_tunneling

        # Initialize tunnel manager if tunneling is enabled
        self.tunnel_manager = TunnelManager() if enable_tunneling else None

    def _check_virtualbox_installation(self) -> bool:
        """Check if VirtualBox is installed and accessible."""
        try:
            result = subprocess.run(
                ["vboxmanage", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"VirtualBox version detected: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"VirtualBox not found or not accessible: {str(e)}")
            raise RuntimeError("VirtualBox is not installed or not accessible")

    def _execute_vbox_command(self, args: list[str]) -> str:
        """Execute a VBoxManage command and return the output."""
        command = ["vboxmanage"] + args
        try:
            print(f"Executing VBoxManage command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(
                f"VBoxManage command failed: {' '.join(command)}, "
                f"error: {e.stderr}, return_code: {e.returncode}"
            )
            raise RuntimeError(f"VBoxManage command failed: {e.stderr}")

    def _is_vm_running(self, vm_name: str) -> bool:
        """Check if a VM is currently running."""
        try:
            output = self._execute_vbox_command(["list", "runningvms"])
            return f'"{vm_name}"' in output
        except RuntimeError:
            return False

    def _start_vm(self, vm_name: str) -> None:
        """Start a VM in headless mode."""
        if self._is_vm_running(vm_name):
            print(f"VM is already running: {vm_name}")
            return

        print(f"Starting VM: {vm_name}")
        try:
            self._execute_vbox_command([
                "startvm", vm_name, "--type", "headless"
            ])

            # Wait for VM to start up
            time.sleep(15)

            if not self._is_vm_running(vm_name):
                raise RuntimeError(f"VM {vm_name} failed to start")

            print(f"VM started successfully: {vm_name}")
        except RuntimeError as e:
            if "VBOX_E_INVALID_OBJECT_STATE" in str(e):
                print(f"VM is already running: {vm_name}")
            else:
                raise

    def _stop_vm(self, vm_name: str) -> None:
        """Stop a VM using ACPI power button."""
        if not self._is_vm_running(vm_name):
            print(f"VM is not running: {vm_name}")
            return

        print(f"Stopping VM: {vm_name}")
        self._execute_vbox_command([
            "controlvm", vm_name, "acpipowerbutton"
        ])

    def _get_vm_ip(self, vm_name: str) -> Optional[str]:
        """Get the IP address of a running VM."""
        try:
            output = self._execute_vbox_command([
                "guestproperty", "get", vm_name,
                "/VirtualBox/GuestInfo/Net/0/V4/IP"
            ])

            # Extract IP from output
            import re
            ip_match = re.search(r'Value: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', output)
            if ip_match:
                return ip_match.group(1)
            return None
        except RuntimeError:
            return None

    def start_vm(
        self,
        vm_name: str,
        config: Config,
        tool_server_port: int = 3333,
    ) -> RunningComputer:
        """
        Start a local VM and return a RunningComputer object.

        Args:
            vm_name: Name of the VirtualBox VM to start
            config: Configuration for the computer
            tool_server_port: Port the tool server runs on (default: 3333)

        Returns:
            RunningComputer object configured for the local VM
        """
        # Generate a unique computer ID
        computer_id = str(uuid.uuid4())

        print(
            f"Starting local VM - computer_id: {computer_id}, vm_name: {vm_name}"
        )

        # Start the VM
        self._start_vm(vm_name)

        # Determine tool server URL
        tool_server_url = self.default_tool_server_url

        if self.enable_tunneling and self.tunnel_manager:
            # Create tunnel for tool server
            tunnel_name = f"{vm_name}_tool_server"
            try:
                tool_server_url = self.tunnel_manager.create_tunnel(tool_server_port, tunnel_name)
            except RuntimeError as e:
                print(f"Failed to create tunnel: {str(e)}")
                # Fallback to localhost URL with warning
                print("WARNING: Using localhost URL - this will only work locally")
                tool_server_url = self.default_tool_server_url

        # Return RunningComputer with configured URL
        return RunningComputer(
            computer_id=computer_id,
            config=config,
            tool_server_url=tool_server_url,
            vnc_url=self.default_vnc_url,  # VNC might need separate tunneling if required
            vnc_auth_key=None,
            vnc_view_only=self.default_vnc_view_only,
        )

    def stop_vm(self, vm_name: str) -> None:
        """Stop a local VM and cleanup tunnels."""
        print(f"Stopping local VM: {vm_name}")

        # Stop associated tunnels if tunnel manager is available
        if self.tunnel_manager:
            tunnel_name = f"{vm_name}_tool_server"
            self.tunnel_manager.stop_tunnel(tunnel_name)

        # Stop the VM
        self._stop_vm(vm_name)

    def is_vm_running(self, vm_name: str) -> bool:
        """Check if a VM is running."""
        return self._is_vm_running(vm_name)

    def get_vm_ip(self, vm_name: str) -> Optional[str]:
        """Get the IP address of a running VM."""
        return self._get_vm_ip(vm_name)

    def cleanup(self) -> None:
        """Cleanup all resources including tunnels."""
        print("Cleaning up LocalVMManager resources")
        if self.tunnel_manager:
            self.tunnel_manager.cleanup()
