#!/usr/bin/env python3
"""
Basic usage example for the AutoComputer SDK.

This example demonstrates how to:
1. Initialize the client
2. List available workflows
3. Run a workflow with streaming responses
"""

import asyncio
import os

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from autocomputer_sdk.client import AutoComputerClient
from autocomputer_sdk.types.computer import Config, RunningComputer, ScreenConfig
from autocomputer_sdk.types.messages.response import RunMessage
from autocomputer_sdk.types.workflow import Workflow
from autocomputer_sdk.validate.workflow_inputs import validate_user_inputs_for_workflow

# Import message renderer
from autocomputer_sdk.render.messages import render_message

load_dotenv()

BASE_URL = os.getenv("BASE_URL") # use the base URL for your deployment given to you by the AutoComputer team
API_KEY = os.getenv("AUTOCOMPUTER_API_KEY")

WORKFLOW_FILE = os.getenv("WORKFLOW_FILE", "examples/workflows/single_prompt.json")

# Initialize Rich console
console = Console()


async def main():
    # Initialize the client
    client = AutoComputerClient(base_url=BASE_URL, api_key=API_KEY)

    loaded_workflow = Workflow.from_json_file(
        WORKFLOW_FILE
    )

    # Statically define user inputs here.
    user_inputs_static = {"task": "Open Hacker News and tell me the top 5 stories"}

    validated_user_inputs = validate_user_inputs_for_workflow(
        loaded_workflow, user_inputs_static
    )

    # Start computer with a nice progress indicator
    with console.status("[bold green]Starting remote computer...", spinner="dots"):
        run_computer: RunningComputer = await client.computer.start(
            config=Config(
                screen=ScreenConfig(width=1440, height=900, display_num=0), os_name="linux", timeout=120
            ).model_dump(),
        )

    # Display computer info in a nice panel
    computer_info = Table.grid(padding=1)
    computer_info.add_column(style="bold cyan", justify="right")
    computer_info.add_column()
    computer_info.add_row("Computer ID:", run_computer.computer_id)
    computer_info.add_row("Screen:", f"{run_computer.config.screen.width}x{run_computer.config.screen.height}")
    computer_info.add_row("OS:", run_computer.config.os_name)

    console.print(Panel(computer_info, title="✅ Remote Computer Started", border_style="green"))

    # Also print the VNC URL separately for easy copying
    console.print(f"\n[bold]🔗 VNC URL:[/bold] [link={run_computer.vnc_url}]{run_computer.vnc_url}[/link]\n")

    result = await client.computer.upload_data_to_file(
        computer_id=run_computer.computer_id,
        file_path="/home/user/test_data.json",
        contents='{"message": "Hello from AutoComputer SDK!"}',
    )
    console.print(f"[green]✓[/green] Uploaded data to file: {result}")

    # Show workflow info
    console.print(f"\n[bold]Starting Workflow:[/bold] {loaded_workflow.workflow_title}")
    console.print(f"[dim]Description:[/dim] {loaded_workflow.workflow_description}\n")

    # Run the workflow with async streaming
    message: RunMessage
    console.print("\n[bold]Streaming workflow execution:[/bold]")

    async for message in client.run.astream(
        workflow=loaded_workflow,
        remote_computer=run_computer,
        user_inputs=validated_user_inputs,  # Use validated inputs
    ):
        await render_message(message, console)

    input("Press Enter to stop the computer...")
    await client.computer.delete(run_computer.computer_id)

if __name__ == "__main__":
    asyncio.run(main())
