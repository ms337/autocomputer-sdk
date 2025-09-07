## AutoComputer SDK

The Python SDK for running natural-language automation workflows with AutoComputer's computer-use agent. Use this SDK to provision remote computers (or connect to local VMs), execute workflows, and stream progress back to your terminal.

## Requirements

- Python 3.10+
- An AutoComputer API key

## Installation

Clone the repo and install in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Configuration

Set your API key in the environment (or a `.env` file):

```bash
export API_KEY="<your-api-key>"
# Optional: If some local scripts expect this name
export AUTOCOMPUTER_API_KEY="$API_KEY"
```

Optionally, create a `.env` file alongside your scripts:

```
API_KEY=<your-api-key>
```

## Quickstart: Single-Prompt Workflow

Use the provided workflow that accepts a single `task` prompt.

1) Open `examples/remote_single_prompt.py` and set `WORKFLOW_FILE` to:

```
examples/workflows/single_prompt.json
```

2) Optionally update the `user_inputs_static` in the script to your desired task.

3) Run it:

```bash
python examples/remote_single_prompt.py
```

This will:
- Start a remote computer
- Upload a small test file
- Stream workflow execution messages to your terminal
- Provide a VNC URL for live viewing

## Multi-step Realistic Example: Web Research and Report

We include a more complete, multi-sequence workflow that performs web research and writes a short report to a file on the remote computer.

- Workflow definition: `examples/workflows/web_research_report.json`
- Runner script: `examples/remote_multi_step_research.py`

To run:

```bash
python examples/remote_multi_step_research.py --topic "vector databases" --results 5 --outfile "/home/user/research_report.md"
```

The script will start a remote computer, execute the workflow with streaming output, and save the generated report on the VM. You can download files afterward using the computer download APIs.

## Other Examples

See `examples/` for more:

- Remote single prompt: `examples/remote_single_prompt.py`
- Local VM runner (VirtualBox): `examples/local_vm_runner.py`
- Filesystem: download a directory as an archive: `examples/filesystem/e2e_download_directory.py`

Each example has inline comments. An `examples/README.md` provides step-by-step usage.

## API Overview

Create a client and access namespaced operations:

```python
from autocomputer_sdk.client import AutoComputerClient
from autocomputer_sdk.types.computer import Config, ScreenConfig

client = AutoComputerClient(base_url="https://api.autocomputer.ai", api_key=os.environ["API_KEY"])

# Start a computer
running = await client.computer.start(
    config=Config(screen=ScreenConfig(width=1440, height=900, display_num=0), os_name="linux").model_dump(),
)

# Run a workflow and stream messages
async for message in client.run.astream(remote_computer=running, workflow=workflow, user_inputs={"task": "..."}):
    ...

# List workflows
workflows = await client.workflows.list()

# Download files
resp = await client.computer.download_file(computer_id=running.computer_id, remote_path="/home/user", is_dir=True)
client.computer.save_downloaded_content(resp, "home_user_backup.tar.gz")
```

Key namespaces:
- `client.workflows`: list, get, save, delete workflows
- `client.computer`: start, get, list, delete; upload/download files; status checks
- `client.run`: run workflows with async streaming
- `client.local`: connect to local VMs and run workflows

## Building Workflows

Workflows are JSON documents (see `examples/workflows/`). They define:
- `workflow_inputs`: runtime parameters
- `sequences`: high-level tasks with ordered steps
- `workflow_execution_instructions.code`: minimal orchestrator code (e.g., calls to `run_sequence`)

Start by copying `examples/workflows/web_research_report.json` and tailoring the inputs, sequences, and steps to your use case.

## Troubleshooting

- Ensure `API_KEY` is set and valid
- Make sure `base_url` points to the correct environment (e.g., `https://api.autocomputer.ai`)
- If streaming appears to hang, check network/firewall rules and try again
- For local VM workflows, confirm your VirtualBox VM name and that the VM image is prepared with the tool server
