#!/usr/bin/env python3
"""
Multi-step realistic example: Web Research and Report

This example shows how to:
- Start a remote computer
- Load a multi-sequence workflow
- Supply runtime inputs from CLI flags
- Stream progress with nicely formatted messages
- Optionally download the generated report locally
"""

import argparse
import asyncio
import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from autocomputer_sdk.client import AutoComputerClient
from autocomputer_sdk.types.computer import Config, RunningComputer, ScreenConfig
from autocomputer_sdk.types.workflow import Workflow
from autocomputer_sdk.validate.workflow_inputs import validate_user_inputs_for_workflow
from autocomputer_sdk.render.messages import render_message


load_dotenv()

BASE_URL = os.getenv("BASE_URL") # use the base URL for your deployment given to you by the AutoComputer team
API_KEY = os.getenv("AUTOCOMPUTER_API_KEY")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Web Research and Report example")
    parser.add_argument("--topic", type=str, default="vector databases", help="Topic to research")
    parser.add_argument("--results", type=int, default=5, help="Number of sources to review")
    parser.add_argument("--outfile", type=str, default="/home/user/research_report.md", help="Output file path on VM")
    parser.add_argument("--download", action="store_true", help="Download the generated report locally after run")
    parser.add_argument("--download-path", type=str, default="./research_report.md", help="Local path to save the report")
    return parser.parse_args()


async def main():
    args = parse_args()

    api_key = os.getenv("AUTOCOMPUTER_API_KEY")
    if not api_key:
        raise RuntimeError("API_KEY environment variable is required")

    console = Console()

    # Initialize client
    client = AutoComputerClient(base_url=BASE_URL, api_key=API_KEY)

    # Load workflow
    workflow_path = os.path.join(
        Path(__file__).parent / "workflows" / "web_research_report.json"
    )
    workflow = Workflow.from_json_file(str(workflow_path))

    # Validate inputs
    user_inputs = {
        "topic": args.topic,
        "num_results": args.results,
        "output_path": args.outfile,
    }
    validated_inputs = validate_user_inputs_for_workflow(workflow, user_inputs)

    # Start computer
    with console.status("[bold green]Starting remote computer...", spinner="dots"):
        run_computer: RunningComputer = await client.computer.start(
            config=Config(
                screen=ScreenConfig(width=1440, height=900, display_num=0),
                os_name="linux",
            ).model_dump(),
            timeout=300,
        )

    info = Table.grid(padding=1)
    info.add_column(style="bold cyan", justify="right")
    info.add_column()
    info.add_row("Computer ID:", run_computer.computer_id)
    info.add_row("Screen:", f"{run_computer.config.screen.width}x{run_computer.config.screen.height}")
    info.add_row("OS:", run_computer.config.os_name)
    console.print(Panel(info, title="✅ Remote Computer Started", border_style="green"))
    console.print(f"\n[bold]🔗 VNC URL:[/bold] [link={run_computer.vnc_url}]{run_computer.vnc_url}[/link]\n")

    console.print(f"\n[bold]Starting Workflow:[/bold] {workflow.workflow_title}")
    console.print(f"[dim]Description:[/dim] {workflow.workflow_description}\n")

    try:
        async for message in client.run.astream(
            remote_computer=run_computer,
            workflow=workflow,
            user_inputs=validated_inputs,
        ):
            await render_message(message, console)
    finally:
        # Optionally download report
        if args.download:
            console.print("\n[bold]📥 Downloading generated report...[/bold]")
            resp = await client.computer.download_file(
                computer_id=run_computer.computer_id,
                remote_path=args.outfile,
                is_dir=False,
            )
            content = base64.b64decode(resp.result.contents)
            Path(args.download_path).write_bytes(content)
            console.print(f"[green]Saved report to[/green] {args.download_path}")

        input("Press Enter to stop the computer...")
        await client.computer.delete(run_computer.computer_id)


if __name__ == "__main__":
    asyncio.run(main())


