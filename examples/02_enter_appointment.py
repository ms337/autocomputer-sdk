#!/usr/bin/env python3
"""
Basic usage example for the AutoComputer SDK.

This example demonstrates how to:
1. Initialize the client
2. List available workflows
3. Run a workflow with streaming responses
"""

import asyncio
from autocomputer_sdk.client import AutoComputerClient
from autocomputer_sdk.types.computer import RunComputer, Config, ScreenConfig
from autocomputer_sdk.types.workflow import Workflow
from autocomputer_sdk.types.messages.response import RunMessage
from autocomputer_sdk.validate.workflow_inputs import validate_user_inputs_for_workflow

from dotenv import load_dotenv
import os

load_dotenv()

# BASE_URL = "http://flow.gcp-staging.autocomputer-zbpxn.ryvn.run"
BASE_URL = "http://localhost:8765"
API_KEY = os.getenv("API_KEY")
# TOOL_SERVER_URL = "https://un3k26xg9pef.share.zrok.io"
TOOL_SERVER_URL = "http://localhost:3333"


def build_computer() -> RunComputer:
    return RunComputer(
        config=Config(
            screen=ScreenConfig(width=1440, height=900, display_num=0), os_name="linux"
        ),
        tool_server_url=TOOL_SERVER_URL,
    )


async def fetch_workflows(client: AutoComputerClient):
    # List all available workflows
    print("Fetching available workflows...")
    workflows = await client.workflows.list()
    print(f"Found {len(workflows)} workflows:")

    for i, workflow in enumerate(workflows):
        print(f"{i+1}. {workflow.title} ({workflow.workflow_id})")

    if not workflows:
        print("No workflows found. Please create a workflow first.")
        return

    return workflows


async def main():
    # Get API key from environment or use a default for demonstration
    api_key = API_KEY

    # Initialize the client
    client = AutoComputerClient(base_url=BASE_URL, api_key=api_key)

    _ = await fetch_workflows(client)

    loaded_workflow = Workflow.from_json_file(
        "/Users/madhav/flow/autocomputer-flow/evaluation/cua_agent/specs/ImplementAI/enter_appointment_new_patient.json"
    )

    # Statically define user inputs here.
    # These will be validated against the loaded_workflow's definitions.
    # Example for 'test_single_prompt.json' which expects a 'task' string input:
    user_inputs_static = {
        "first_name": "AC",
        "last_name": "Testing 6",
        "title": "Ms.",
        "insurance_type": "Private",
        "reason_for_appointment": "Hygiene Appointment",
        "selected_provider": "JP",
        "appointment_date": "30/12/25",
        "appointment_time": "1:00 PM",
        "phone_number": "+441201294798",
        "email": "testXYZ@testing.ai",
        "gender": "Not Specified",
        "date_of_birth": "01/02/01",
        "address": "2 Test Street, Bristol",
        "postcode": "brs-909",
        "referred_by_type": "Other",  # use either Other or Patient
        "referred_by_value": "FAM",  # use mapped code here
        "additional_medical_information": "None",
        "created_at": "2025-04-28 14:50:13",
    }

    validated_user_inputs = validate_user_inputs_for_workflow(
        loaded_workflow, user_inputs_static
    )

    # Create a RemoteComputer configuration
    run_computer = build_computer()

    # Run the workflow with async streaming
    message: RunMessage
    print("\nStreaming workflow execution:")

    async for message in client.run.astream(
        workflow=loaded_workflow,
        remote_computer=run_computer,
        user_inputs=validated_user_inputs,  # Use validated inputs
    ):
        if message.type == "run_started":
            print("▶️ Workflow run started")
        elif message.type == "sequence_status":
            status = "✅" if message.success else "❌"
            error_info = f" - Error: {message.error}" if message.error else ""
            print(f"{status} Sequence {message.sequence_id}{error_info}")
        elif message.type == "assistant":
            print(f"💬 Assistant message received: \n{message.content}\n")
        elif message.type == "error":
            print(f"⚠️ Error: {message.error}")
        elif message.type == "run_completed":
            print("✅ Workflow completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
