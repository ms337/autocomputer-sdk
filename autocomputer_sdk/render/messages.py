#!/usr/bin/env python3
"""
Message renderer module for AutoComputer SDK examples.

This module provides clean rendering functions for RunMessage objects
using Rich formatting. It can be imported and used across different examples.
"""

import json
import re
from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from autocomputer_sdk.types.messages.response import RunMessage


def is_base64_string(s: str) -> bool:
    """Check if a string looks like base64 encoded data."""
    if len(s) < 100:  # Short strings are probably not base64 screenshots
        return False
    # Check for common base64 patterns
    base64_pattern = re.compile(r'^[A-Za-z0-9+/]{100,}={0,2}$')
    return bool(base64_pattern.match(s))


def truncate_long_string(s: str, max_length: int = 200) -> str:
    """Truncate long strings, especially base64 data."""
    if is_base64_string(s):
        return "[base64 image data omitted]"
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s


def format_tool_input(input_dict: Dict[str, Any]) -> str:
    """Format tool input dictionary for display."""
    formatted = {}
    for key, value in input_dict.items():
        if isinstance(value, str):
            formatted[key] = truncate_long_string(value)
        elif isinstance(value, dict):
            # Recursively format nested dictionaries
            formatted[key] = format_tool_input(value)
        else:
            formatted[key] = value
    return json.dumps(formatted, indent=2)


async def render_message(message: RunMessage, console: Console):
    """Render a message using Rich formatting."""

    if message.type == "run_started":
        console.print(Panel("🚀 [bold green]Workflow Started[/bold green]", expand=False))

    elif message.type == "sequence_started":
        console.print(f"\n[bold blue]▶️  Starting Sequence:[/bold blue] {message.sequence_id}")

    elif message.type == "sequence_status":
        status_icon = "✅" if message.success else "❌"
        status_color = "green" if message.success else "red"
        status_text = "Success" if message.success else "Failed"

        status_msg = f"{status_icon} [bold {status_color}]Sequence {message.sequence_id}: {status_text}[/bold {status_color}]"
        if message.error:
            status_msg += f"\n   [red]Error: {message.error}[/red]"
        console.print(Panel(status_msg, expand=False))

    elif message.type == "assistant":
        # Handle content as ACContentBlock type
        content = message.content

        if hasattr(content, 'type'):
            content_type = content.type

            if content_type == "tool_use":
                # Tool use message
                tool_panel = Panel.fit(
                    f"[bold cyan]Tool:[/bold cyan] {getattr(content, 'name', 'unknown')}\n"
                    f"[dim]Input:[/dim]\n{format_tool_input(getattr(content, 'input', {}))}",
                    title="🔨 Tool Execution",
                    border_style="blue"
                )
                console.print(tool_panel)

            elif content_type == "tool_use_result":
                # Tool result message
                tool_result = getattr(content, 'result', {})
                result_lines = []
                
                if hasattr(tool_result, '__dict__') or isinstance(tool_result, dict):
                    # Check for base64_image field specifically
                    base64_image = getattr(tool_result, 'base64_image', None) if hasattr(tool_result, '__dict__') else tool_result.get('base64_image')
                    if base64_image:
                        result_lines.append("[bold]Screenshot:[/bold] [dim italic]📸 Image captured[/dim italic]")
                    
                    # Always show output if it exists and is not base64
                    output = getattr(tool_result, 'output', None) if hasattr(tool_result, '__dict__') else tool_result.get('output')
                    if output:
                        output_str = str(output)
                        if not is_base64_string(output_str):
                            # For non-base64 output, show it (truncated if needed)
                            result_lines.append(f"[bold]Output:[/bold] {truncate_long_string(output_str, 500)}")
                    
                    # Check for error
                    error = getattr(tool_result, 'error', None) if hasattr(tool_result, '__dict__') else tool_result.get('error')
                    if error:
                        result_lines.append(f"[bold red]Error:[/bold red] {error}")
                
                result_panel = Panel(
                    "\n".join(result_lines) if result_lines else "[dim]No output[/dim]",
                    title="🔧 Tool Result",
                    border_style="green" if not (hasattr(tool_result, 'error') and getattr(tool_result, 'error', None)) else "red"
                )
                console.print(result_panel)

            elif content_type == "text":
                # Regular text message
                text_content = getattr(content, 'text', '')
                text = Text(text_content)
                console.print(Panel(text, title="💬 Assistant", border_style="blue"))

            elif content_type == "thinking":
                # Thinking message (usually hidden, but we'll show it dimmed)
                thinking_content = getattr(content, 'thinking', '')
                console.print(f"[dim italic]🤔 {thinking_content}[/dim italic]")

            else:
                # Unknown content type
                console.print(f"[yellow]Unknown assistant message type: {content_type}[/yellow]")
        else:
            # Fallback for unstructured content
            console.print(Panel(str(content), title="💬 Assistant", border_style="yellow"))

    elif message.type == "error":
        console.print(Panel(f"[bold red]⚠️  Error: {message.error}[/bold red]", border_style="red"))

    elif message.type == "run_completed":
        console.print(Panel("✅ [bold green]Workflow Completed Successfully![/bold green]", expand=False))

    else:
        # Unknown message type
        console.print(f"[yellow]Unknown message type: {message.type}[/yellow]")
