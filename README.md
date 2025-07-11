# AutoComputer SDK

The Python SDK to use AutoComputer for performing automations described through natural language defined workflows using AutoComputer's computer use agent. 

This SDK let's you provision computers and run automation workflows easily on them.

## Installation

Clone the repo, and then `cd ` into the folder and then run: 

```bash
pip install -e .
```

## Quick Start

To quick start, use AutoComputer's Automation Agent with a workflow that takes a single prompt task asks the agent to perform it. 


Steps: 

1. Create a Venv and install the SDK
2. Set the API key as an env var or in a `.env` file that has been given to you by the AutoComputer team. 
3. Open the runner script (see below) and set the path to the workflow file (see below).
4. Set the `task` input in the runner script. 
4. Run the runner script. This will render UI in the terminal that will start the workflow. 


### Workflow File
The workflow file is in `examples/workflows/single_prompt.json` — this is a structured data file that servers as an "automation definition" to AutoComputer. This particular one is definining a workflow that takes a single prompt and runs it. 

Each workflow takes some input parameters — i.e. arguments to an automation program. The `single_prompt.json` workflow takes a single parameter called `task` which is the prompt of the task to be performed.

### Runner Script
The runner scirpt is in `examples/remote_single_prompt.py`


## Building Workflows

Coming soon - but message the AutoComputer team and they will help you out here. 

## API Reference

Coming soon.
