from autocomputer_sdk.types.computer import RunComputer
from autocomputer_sdk.types.workflow import Workflow
from pydantic import BaseModel
from typing import Dict, Any


class CreateRunRequest(BaseModel):
    remote_computer: RunComputer
    workflow: Workflow
    user_inputs: Dict[str, Any]
