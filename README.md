# AutoComputer SDK

[![PyPI version](https://img.shields.io/pypi/v/autocomputer-sdk.svg)](https://pypi.org/project/autocomputer-sdk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/autocomputer-sdk.svg)](https://pypi.org/project/autocomputer-sdk/)
[![License](https://img.shields.io/github/license/autocomputer-ai/sdk.svg)](https://github.com/autocomputer-ai/sdk/blob/main/LICENSE)

A well-structured Python SDK for the AutoComputer Flow API with namespaced routes and strong typing.

## Features

- 🔀 **Namespaced routes**: Access API functionality using intuitive namespaces (e.g., `client.workflows.list()`)
- 📊 **Strong typing**: Fully typed request and response objects for better IDE support and error checking
- 🔄 **Async streaming support**: Real-time updates as your workflows execute
- 🛠️ **Modern Python**: Built with modern Python practices and type annotations

## Installation

```bash
pip install autocomputer-sdk
```

## Quick Start

```python
import asyncio
import os
from autocomputer_sdk.client import AutoComputerClient
from autocomputer_sdk.types.computer import RunComputer, Config, ScreenConfig
from autocomputer_sdk.types.workflow import Workflow

# Example: Load API key from environment variable or replace with your key
API_KEY = os.getenv("AUTOCOMPUTER_API_KEY", "your-api-key")
BASE_URL = os.getenv("AUTOCOMPUTER_BASE_URL", "https://api.autocomputer.ai")

async def main():
    # Initialize the client
    client = AutoComputerClient(
        base_url=BASE_URL, 
        api_key=API_KEY
    )
    
    # 1. List available workflows (optional, to get a workflow_id)
    # workflows_summary = await client.workflows.list()
    # if not workflows_summary:
    #     print("No workflows found.")
    #     return
    # print(f"Found {len(workflows_summary)} workflows. Example: {workflows_summary[0].title}")

    # 2. Define the RunComputer configuration
    remote_computer = RunComputer(
        config=Config(
            screen=ScreenConfig(),
            os_name="linux"  # Or "darwin", "win32"
        ),
        host_ip="127.0.0.1", # IP of the machine where the tool server is running
        tool_server_port=3333
    )

    # 3. Load or define your Workflow object
    # Option A: Load from a JSON file (replace with your actual path)
    # Ensure you have a workflow JSON file, e.g., 'my_workflow.json'
    # For this example, we'll assume a placeholder structure if the file doesn't exist
    try:
        loaded_workflow = Workflow.from_json_file("path/to/your/workflow.json")
    except FileNotFoundError:
        print("Workflow file not found. Using a placeholder workflow structure for demonstration.")
        # This is a minimal placeholder. Replace with actual workflow data.
        loaded_workflow = Workflow(
            schema_version="v1",
            workflow_computer=WorkflowComputer(
                os="linux", 
                computerName="example-vm", 
                computerType="remoteDesktop",
                screenConfig=ScreenConfig()
            ),
            workflow_title="My Example Workflow",
            workflow_description="A sample workflow for demonstration.",
            workflow_inputs=[],
            sequences=[],
            workflow_execution_instructions=WorkflowExecution(instructions=[], code=[])
        )

    # 4. Define user inputs for the workflow (if any)
    user_inputs = {
        "task_description": "Summarize the main points of the provided document."
        # Add other inputs as defined in your workflow_inputs
    }
    
    # 5. Run the workflow with streaming responses
    print(f"\nRunning workflow: {loaded_workflow.workflow_title}")
    async for message in client.run.astream(
        remote_computer=remote_computer,
        workflow=loaded_workflow,
        user_inputs=user_inputs
    ):
        if message.type == "run_started":
            print("▶️ Workflow run started")
        elif message.type == "sequence_status":
            status = "✅" if message.success else "❌"
            error_info = f" - Error: {message.error}" if message.error else ""
            print(f"{status} Sequence {message.sequence_id}{error_info}")
        elif message.type == "assistant":
            print(f"💬 Assistant: {message.content}")
        elif message.type == "error":
            print(f"⚠️ Error: {message.error}")
        elif message.type == "run_completed":
            print("✅ Workflow completed successfully")

if __name__ == "__main__":
    # Note: You might need to import WorkflowComputer and WorkflowExecution for the placeholder
    from autocomputer_sdk.types.workflow import WorkflowComputer, WorkflowExecution 
    asyncio.run(main())
```

## API Reference


The API has 3 parts:
1. Client
2. Computer
3. Workflow


### Client Initialization

```python
from autocomputer_sdk.client import AutoComputerClient

client = AutoComputerClient(
    base_url="https://api.autocomputer.ai",  # API base URL
    api_key="your-api-key"                   # Your API key
)
```

### `RunComputer` Object

When running a workflow, you need to provide a `RunComputer` object that specifies the target execution environment.

```python
from autocomputer_sdk.types.computer import RunComputer, Config, ScreenConfig

remote_computer = RunComputer(
    config=Config(
        screen=ScreenConfig(
            width=1920,       # Desired screen width
            height=1080,      # Desired screen height
            display_num=0     # Display number (usually 0)
        ),
        os_name="linux"     # Operating system: "linux", "darwin", or "win32"
    ),
    host_ip="127.0.0.1",    # IP address of the machine running the tool server
    tool_server_port=3333   # Port of the tool server on that machine
)
```

### `Workflow` Object

A `Workflow` object defines the tasks to be executed. You can load it from a JSON file, create it from a dictionary (e.g., after fetching from the API), or construct it programmatically.

```python
from autocomputer_sdk.types.workflow import Workflow

# Option 1: Load from a JSON file
# workflow = Workflow.from_json_file("path/to/your_workflow.json")

# Option 2: Create from a dictionary (e.g., from API response)
# workflow_dict = await client.workflows.get(workflow_id="some-workflow-id")
# workflow = Workflow.from_dict(workflow_dict)

# Option 3: Minimal programmatic creation (refer to Workflow schema for full structure)
# from autocomputer_sdk.types.workflow import WorkflowComputer, WorkflowExecution, ScreenConfig # (add other necessary imports)
# workflow = Workflow(
#     schema_version="v1",
#     workflow_computer=WorkflowComputer(os="linux", computerName="dev", computerType="remoteDesktop", screenConfig=ScreenConfig(width=1920,height=1080,display_num=0)),
#     workflow_title="My Custom Workflow",
#     workflow_description="...",
#     workflow_inputs=[], 
#     sequences=[], 
#     workflow_execution_instructions=WorkflowExecution(instructions=[], code=[])
# )
```

### Workflows Namespace (`client.workflows`)

#### List Workflows

Returns a list of `WorkflowSummary` objects.
```python
workflow_summaries = await client.workflows.list()
for wf_summary in workflow_summaries:
    print(f"ID: {wf_summary.workflow_id}, Title: {wf_summary.title}")
```

#### Get Workflow by ID

Returns a workflow definition as a Python dictionary. You can convert this to a `Workflow` object if needed.
```python
from autocomputer_sdk.types.workflow import Workflow

workflow_dict = await client.workflows.get(workflow_id="your-workflow-id")
# To use with client.run.astream, convert to Workflow object:
# workflow_obj = Workflow.from_dict(workflow_dict)
```

#### Save Workflow

Saves a workflow. The `workflow` parameter should be a dictionary representing the workflow.
If you have a `Workflow` object, use `workflow.model_dump()`.
```python
# Assume 'my_workflow_object' is an instance of the Workflow model
# workflow_data_dict = my_workflow_object.model_dump()

# Or, if you have a dictionary directly:
workflow_data_dict = {
    "schema_version": "v1",
    "workflow_computer": {
        "os": "linux", 
        "computerName": "prod-server", 
        "computerType": "remoteDesktop",
        "screenConfig": {"width": 1920, "height": 1080, "display_num": 0}
    },
    "workflow_title": "Production Task",
    "workflow_description": "Handles daily production tasks.",
    "workflow_inputs": [],
    "sequences": [],
    "workflow_execution_instructions": {"instructions": [], "code": []}
}

workflow_summary = await client.workflows.save(
    workflow=workflow_data_dict,
    user_id="optional-user-id" # Optional
)
print(f"Workflow saved with ID: {workflow_summary.workflow_id}")
```

#### Delete Workflow

```python
success = await client.workflows.delete(
    workflow_id="workflow-id-to-delete",
    user_id="optional-user-id" # Optional
)
if success:
    print("Workflow deleted successfully.")
```

### Run Namespace (`client.run`)

#### Stream Workflow Execution (`astream`)

Runs a workflow and streams responses back asynchronously.

```python
# Ensure 'remote_computer' (RunComputer object) and 'workflow_to_run' (Workflow object) are defined
# user_inputs_dict = {"input_name": "input_value"}

async for message in client.run.astream(
    remote_computer=remote_computer, # Instance of RunComputer
    workflow=workflow_to_run,        # Instance of Workflow
    user_inputs=user_inputs_dict     # Optional dictionary of inputs
):
    if message.type == "run_started":
        print("▶️ Workflow run started")
    elif message.type == "sequence_status":
        status = "✅" if message.success else "❌"
        error_info = f" - Error: {message.error}" if message.error else ""
        print(f"{status} Sequence {message.sequence_id}{error_info}")
    elif message.type == "assistant":
        print(f"💬 Assistant: {message.content}")
    elif message.type == "error":
        print(f"⚠️ Error: {message.error}")
    elif message.type == "run_completed":
        print("✅ Workflow completed successfully")
```

## Response Message Types

The SDK provides strongly typed message classes for streaming responses from `client.run.astream`:

- `RunStartedMessage`: Indicates a workflow run has started.
- `RunSequenceStatusMessage`: Reports the status of a sequence execution (`sequence_id`, `success`, `error`).
- `RunAssistantMessage`: Contains output from the assistant (`content`).
- `RunErrorMessage`: Indicates an error occurred during the run (`error`).
- `RunCompletedMessage`: Indicates a workflow run has completed successfully.

Refer to `autocomputer_sdk.types.messages.response` for detailed definitions.

## Development

### Requirements

- Python 3.9+
- `httpx` for HTTP requests
- `pydantic` for data validation and serialization

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.