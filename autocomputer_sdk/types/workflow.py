from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class OSName(str, Enum):
    DARWIN = "darwin"
    WIN32 = "win32"
    LINUX = "linux"


SchemaVersions = Literal["v1"]


class InputType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    LIST = "list"
    FILE = "file"
    DIRECTORY = "directory"


class FileFilter(BaseModel):
    name: str
    extensions: List[str]


class WorkflowInput(BaseModel):
    input_title: str
    input_description: str
    input_type: InputType
    input_name: str
    default_value: Optional[Any] = None
    file_filters: Optional[List[FileFilter]] = None


class WorkflowStep(BaseModel):
    title: str
    actions: List[str]


class WorkflowSequence(BaseModel):
    sequence_title: str
    sequence_id: str
    sequence_description: str
    sequence_inputs: List[str]
    steps: List[WorkflowStep]


class WorkflowExecution(BaseModel):
    instructions: List[str]
    code: List[str]


class ScreenConfig(BaseModel):
    width: int
    height: int
    display_num: int


class ComputerType(str, Enum):
    LOCAL_DESKTOP = "localDesktop"
    REMOTE_DESKTOP = "remoteDesktop"
    LOCAL_VM = "localVM"


class WorkflowComputer(BaseModel):
    os: OSName
    computerName: str
    computerType: ComputerType
    ovaFilePath: Optional[str] = None
    screenConfig: ScreenConfig


class FileInputParameter(BaseModel):
    name: str
    path: str


class Workflow(BaseModel):
    schema_version: Literal["v1"]
    workflow_computer: WorkflowComputer
    workflow_title: str
    workflow_description: str
    workflow_inputs: List[WorkflowInput]
    sequences: List[WorkflowSequence]
    workflow_execution_instructions: WorkflowExecution
    workflow_path: Optional[str] = None
    workflow_id: Optional[str] = None  # TODO: make this required later

    @classmethod
    def from_json_string(cls, json_string: str) -> "Workflow":
        """Loads a Workflow instance from a JSON string."""
        return cls.model_validate_json(json_string)

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> "Workflow":
        """Loads a Workflow instance from a Python dictionary."""
        return cls.model_validate(data_dict)

    @classmethod
    def from_json_file(cls, file_path: str) -> "Workflow":
        """Loads a Workflow instance from a JSON file."""
        import json

        with open(file_path) as f:
            data = json.load(f)
        return cls.from_dict(data)


class WorkflowSummary(BaseModel):
    """Summary information about a workflow returned when listing workflows."""

    workflow_id: str
    title: str
    description: str
