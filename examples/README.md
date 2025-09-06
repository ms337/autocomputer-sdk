## Examples

This directory contains runnable scripts demonstrating the AutoComputer SDK.

Prerequisites:
- Python 3.10+
- `pip install -e .`
- `export API_KEY=<your-api-key>` (or `.env` with `API_KEY=...`)

### Remote single prompt

Run a simple workflow that accepts a single `task` string.

1) Set the workflow path in `examples/remote_single_prompt.py`:

```
WORKFLOW_FILE = "examples/workflows/single_prompt.json"
```

2) Optionally edit `user_inputs_static` for your task.

3) Execute:

```bash
python examples/remote_single_prompt.py
```

### Multi-step web research and report

Performs web research across multiple sources, synthesizes findings, and writes a markdown report.

- Workflow: `examples/workflows/web_research_report.json`
- Runner: `examples/remote_multi_step_research.py`

Run with defaults:

```bash
python examples/remote_multi_step_research.py
```

Customize inputs:

```bash
python examples/remote_multi_step_research.py \
  --topic "retrieval augmented generation" \
  --results 7 \
  --outfile "/home/user/rag_report.md" \
  --download --download-path ./rag_report.md
```

### Local VM runner (VirtualBox)

Demonstrates connecting to a local VirtualBox VM and running a workflow over WebSocket.

```bash
python examples/local_vm_runner.py
```

Make sure you update the VM name in the script to match your VirtualBox image and that the local tool server is available.

### Filesystem: download directory

End-to-end example showing how to upload some test files in `/home/user`, then download the entire directory as a tar.gz archive and verify its contents.

```bash
python examples/filesystem/e2e_download_directory.py
```


