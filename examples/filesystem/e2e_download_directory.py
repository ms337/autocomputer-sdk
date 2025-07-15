#!/usr/bin/env python3
"""
AutoComputer SDK Example: Download Directory as Archive

This example demonstrates the new directory download functionality:
1. Start a remote computer
2. Create some files in /home/user to establish a directory structure
3. Download the entire /home/user directory as a tar.gz archive
4. Verify the archive can be extracted and contains the expected files

This showcases the new is_dir=True feature for downloading directories.
"""

import asyncio
import base64
import os
import tarfile
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from autocomputer_sdk.client import AutoComputerClient
from autocomputer_sdk.types.computer import Config, RunningComputer, ScreenConfig

load_dotenv()

BASE_URL = "http://localhost:8765"
API_KEY = os.getenv("API_KEY")


# Initialize Rich console
console = Console()


async def main():
    if not API_KEY:
        console.print("[red]❌ API_KEY not found in environment variables[/red]")
        return

    # Initialize the client
    client = AutoComputerClient(base_url=BASE_URL, api_key=API_KEY)

    console.print("[bold]🚀 Starting Directory Download Test[/bold]\n")

    # Start computer
    with console.status("[bold green]Starting remote computer...", spinner="dots"):
        run_computer: RunningComputer = await client.computer.start(
            config=Config(
                screen=ScreenConfig(width=1440, height=900, display_num=0), 
                os_name="linux", 
                timeout=300
            ).model_dump(),
        )

    console.print(f"[green]✅ Computer started:[/green] {run_computer.computer_id}")

    try:
        # Step 1: Create some test files to populate /home/user
        console.print("\n[bold]📝 Step 1: Creating test files in /home/user...[/bold]")
        
        test_files = {
            "/home/user/readme.txt": "Welcome to the user directory!\nThis is a test file for directory download.",
            "/home/user/config.json": '{\n  "app_name": "test_app",\n  "version": "1.0.0",\n  "debug": true\n}',
            "/home/user/documents/note.md": "# My Notes\n\n- This is a markdown file\n- Created for testing\n- Directory download works!",
            "/home/user/scripts/hello.sh": "#!/bin/bash\necho 'Hello from a shell script!'\necho 'Directory: /home/user/scripts'",
        }

        # Upload the test files
        for file_path, content in test_files.items():
            await client.computer.upload_data_to_file(
                computer_id=run_computer.computer_id,
                file_path=file_path,
                contents=content
            )
            console.print(f"[dim]Created:[/dim] {file_path}")

        console.print(f"[green]✅ Created {len(test_files)} test files[/green]")

        # Step 2: Test single file download (existing functionality)
        console.print("\n[bold]📥 Step 2: Testing single file download (is_dir=False)...[/bold]")
        
        single_file = await client.computer.download_file(
            computer_id=run_computer.computer_id,
            remote_path="/home/user/readme.txt",
            is_dir=False  # Explicit file download
        )
        
        # Decode the base64 content
        decoded_content = base64.b64decode(single_file.result.contents).decode('utf-8')
        
        console.print(f"[green]✅ Single file downloaded![/green]")
        console.print(f"[dim]File size:[/dim] {len(decoded_content)} characters")
        console.print(f"[dim]Is directory:[/dim] {single_file.result.is_dir}")
        console.print(Panel(
            decoded_content.strip()[:200] + ("..." if len(decoded_content) > 200 else ""), 
            title="📄 File Content Preview", 
            border_style="blue"
        ))

        # Step 3: Test directory download (new functionality)
        console.print("\n[bold]📁 Step 3: Testing directory download (is_dir=True)...[/bold]")
        
        directory_download = await client.computer.download_file(
            computer_id=run_computer.computer_id,
            remote_path="/home/user",
            is_dir=True,  # NEW: Explicit directory download
            max_size_bytes=50 * 1024 * 1024  # 50MB limit
        )
        
        console.print(f"[green]✅ Directory downloaded as archive![/green]")
        console.print(f"[dim]Archive size:[/dim] {len(directory_download.result.contents)} characters (base64)")
        console.print(f"[dim]Is directory:[/dim] {directory_download.result.is_dir}")
        
        # Step 4: Save and examine the archive
        console.print("\n[bold]🔍 Step 4: Extracting and examining archive...[/bold]")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the archive using the helper method
            archive_path = os.path.join(temp_dir, "home_user_backup.tar.gz")
            success = client.computer.save_downloaded_content(directory_download, archive_path)
            
            if not success:
                console.print("[red]❌ Failed to save archive[/red]")
                return False
            
            # Get archive info
            archive_size = os.path.getsize(archive_path)
            console.print(f"[green]✅ Archive saved:[/green] {archive_size} bytes")
            
            # Extract and examine contents
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(extract_dir)
                
                # List contents (safely handle symlinks and broken files)
                extracted_files = []
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, extract_dir)
                        try:
                            # Skip symlinks and get file size safely
                            if os.path.islink(file_path):
                                file_size = 0  # Skip symlinks
                            else:
                                file_size = os.path.getsize(file_path)
                            extracted_files.append((rel_path, file_size))
                        except (OSError, FileNotFoundError):
                            # Skip files that can't be accessed
                            extracted_files.append((rel_path, 0))
                
                # Create a table to show extracted files (limit to first 20 for readability)
                table = Table(title="📦 Extracted Archive Contents (First 20 Files)")
                table.add_column("File Path", style="cyan")
                table.add_column("Size (bytes)", justify="right", style="magenta")
                
                for file_path, size in sorted(extracted_files)[:20]:
                    table.add_row(file_path, str(size))
                
                if len(extracted_files) > 20:
                    table.add_row(f"... and {len(extracted_files) - 20} more files", "...")
                
                console.print(table)
                
                # Verify our test files are in the archive
                console.print("\n[bold]✅ Verification Results:[/bold]")
                
                verification_count = 0
                for original_path in test_files.keys():
                    # Convert /home/user/file.txt to user/file.txt (tar strips leading /)
                    expected_in_archive = original_path.replace("/home/", "")
                    
                    # Look for exact matches or files containing our expected path
                    found = any(
                        expected_in_archive in extracted_path or 
                        extracted_path.endswith(expected_in_archive.split('/')[-1])
                        for extracted_path, _ in extracted_files
                    )
                    status = "✅" if found else "❌"
                    console.print(f"{status} Found: {expected_in_archive}")
                    if found:
                        verification_count += 1
                
                console.print(f"\n[bold]📊 Summary:[/bold]")
                console.print(f"• Created files: {len(test_files)}")
                console.print(f"• Files found in archive: {verification_count}")
                console.print(f"• Total extracted files: {len(extracted_files)}")
                console.print(f"• Archive size: {archive_size:,} bytes")
                
                if verification_count >= len(test_files):
                    console.print(f"\n[bold green]🎉 SUCCESS: Directory download functionality working perfectly![/bold green]")
                    console.print(f"[green]• Single file download: ✅")
                    console.print(f"[green]• Directory archive download: ✅")  
                    console.print(f"[green]• Archive extraction: ✅")
                    console.print(f"[green]• File verification: ✅")
                    return True
                else:
                    console.print(f"\n[bold yellow]⚠️  PARTIAL SUCCESS: Some files missing from archive[/bold yellow]")
                    return False
        
    except Exception as e:
        console.print(f"\n[red]❌ Error during test:[/red] {str(e)}")
        import traceback
        console.print(f"[red]Traceback:[/red] {traceback.format_exc()}")
        return False
        
    finally:
        # Clean up
        console.print(f"\n[dim]Cleaning up computer...[/dim]")
        try:
            await client.computer.delete(run_computer.computer_id)
            console.print(f"[green]✅ Computer deleted successfully[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Error deleting computer:[/yellow] {str(e)}")


async def demo_usage():
    """Show example usage without actually running the test."""
    console.print("[bold]📖 Directory Download API Usage Examples:[/bold]\n")
    
    code_examples = [
        ("Download a single file", """
# Download a single file (existing functionality, now returns base64)
response = await client.computer.download_file(
    computer_id="your-computer-id",
    remote_path="/home/user/document.txt",
    is_dir=False  # Explicit file download
)

# Decode the content
content = base64.b64decode(response.result.contents).decode('utf-8')
print(f"File content: {content}")
        """),
        
        ("Download a directory as archive", """
# Download entire directory as tar.gz archive (NEW FEATURE)
response = await client.computer.download_file(
    computer_id="your-computer-id", 
    remote_path="/home/user",
    is_dir=True,  # NEW: Directory download
    max_size_bytes=100 * 1024 * 1024  # 100MB limit
)

        # Save to local file using helper method
        success = client.computer.save_downloaded_content(response, "backup.tar.gz")
if success:
    print("Directory saved as backup.tar.gz")
        """),
        
        ("Manual archive handling", """
# Or handle the archive manually
import base64
import tarfile

response = await client.computer.download_file(
    computer_id="your-computer-id",
    remote_path="/home/user", 
    is_dir=True
)

# Decode base64 to get archive bytes
archive_bytes = base64.b64decode(response.result.contents)

# Save or extract directly
with open("my_archive.tar.gz", "wb") as f:
    f.write(archive_bytes)

# Or extract in memory
import io
with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
    tar.extractall("extracted_files/")
        """)
    ]
    
    for title, code in code_examples:
        console.print(Panel(code.strip(), title=f"💡 {title}", border_style="green"))
        console.print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        asyncio.run(demo_usage())
    else:
        success = asyncio.run(main())
        if success:
            console.print(f"\n[bold green]✅ OVERALL RESULT: Directory download test passed![/bold green]")
            console.print(f"[dim]Run with --demo flag to see usage examples[/dim]")
        else:
            console.print(f"\n[bold red]❌ OVERALL RESULT: Test failed - check errors above[/bold red]")