"""
Example: Running workflows on local VirtualBox VMs

This example demonstrates how to:
1. Initialize the AutoComputer client with a VM manager
2. Start a VirtualBox VM
3. Run a workflow on the local VM via WebSocket
4. Clean up resources
"""

import os
import asyncio
import logging
from autocomputer_sdk import AutoComputerClient, VMConfig, LocalVMManager
from autocomputer_sdk.types.workflow import Workflow
from dotenv import load_dotenv

logging.basicConfig(level=logging.WARNING)

load_dotenv()

API_KEY = os.getenv("AUTOCOMPUTER_API_KEY") 
LOCAL_VBOX_VM_NAME = "ac-ubuntu-v7" # the name of the VM loaded into virtualbox

WORKFLOW_PATH = "/Users/madhav/cursor_repos/flow/autocomputer-flow/evaluation/cua_agent/specs/generic_evals/linux/test_single_prompt.json"
USER_INPUTS = { # the user inputs for the workflow
    "task": "Find best shawarma in mission bay"
}

BASE_URL = "https://api.autocomputer.ai"

async def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the client
    client = AutoComputerClient(
        base_url=BASE_URL,
        api_key=API_KEY
    )
    
    # Initialize VM manager
    vm_manager = LocalVMManager()
    
    # Set the VM manager on the client
    client.set_local_vm_manager(vm_manager)
    
    try:
        # Start a VirtualBox VM
        print("Starting VirtualBox VM...")
        vm = await client.local.vm.start_vbox(
            vm_name=LOCAL_VBOX_VM_NAME,  # Updated to use your actual VM name
            screen_width=1440,
            screen_height=900,
            wait_for_tool_server=True,
            timeout=120
        )
        print(f"VM started: {vm.name} (ID: {vm.computer_id})")
        
        
        workflow = Workflow.from_json_file(
            WORKFLOW_PATH
        )
        
        # Define user inputs for the workflow
        user_inputs = USER_INPUTS
        
        # Run the workflow on the local VM
        print("Running workflow on local VM...")
        async for message in client.local.connect_and_run_workflow(
            workflow=workflow,
            user_inputs=user_inputs,
            vm_instance=vm  # Use the VM we just started
        ):
            if message.type == "run_started":
                print("Workflow execution started")
            elif message.type == "assistant":
                if message.content['type'] == "tool_use_result":
                    print(f"Assistant: {message.content['result']['output']}")
                else:
                    print(f"Assistant: {message.content}")
            elif message.type == "sequence_status":
                status = "✓" if message.success else "✗"
                print(f"{status} Sequence {message.sequence_id}: {message.success}")
                if message.error:
                    print(f"Error: {message.error}")
            elif message.type == "error":
                print(f"Error: {message.error}")
                break
            elif message.type == "run_completed":
                print("Workflow completed successfully!")
                break
                
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Clean up: stop the VM
        if 'vm' in locals():
            print("Stopping VM...")
            await client.local.vm.stop_vbox(vm.name)
            await asyncio.sleep(10) # wait for 10 seconds to ensure the VM is stopped
            print("VM stopped")
        
        # Clean up client resources
        client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 