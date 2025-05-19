from typing import List, Dict, Any
from autocomputer_sdk.types.workflow import WorkflowInput, Workflow, InputType


def validate_user_inputs_for_workflow(
    workflow: Workflow, provided_inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """Validates provided inputs against workflow definitions and prepares them."""
    workflow_inputs_defs: List[WorkflowInput] = workflow.workflow_inputs
    final_inputs: Dict[str, Any] = {}
    defined_input_names = {wf_input.input_name for wf_input in workflow_inputs_defs}

    if len(workflow_inputs_defs) > 1 and len(provided_inputs) == 0:
        raise ValueError(
            f"Workflow has multiple inputs ({len(workflow_inputs_defs)}) but no inputs were provided"
        )
    if len(workflow_inputs_defs) == 0 and len(provided_inputs) > 0:
        raise ValueError(
            f"Workflow has no inputs but {len(provided_inputs)} inputs were provided"
        )

    # Check for unexpected inputs provided by the user
    for provided_name in provided_inputs:
        if provided_name not in defined_input_names:
            raise ValueError(
                f"Unexpected input '{provided_name}' provided. Valid inputs are: {', '.join(sorted(list(defined_input_names)))}"
            )

    for wf_input in workflow_inputs_defs:
        input_name = wf_input.input_name
        expected_type = wf_input.input_type
        default_value = wf_input.default_value

        if input_name in provided_inputs:
            value = provided_inputs[input_name]
            # Validate type
            valid_type = False
            if expected_type == InputType.STRING and isinstance(value, str):
                valid_type = True
            elif expected_type == InputType.NUMBER and isinstance(value, (int, float)):
                valid_type = True
            elif expected_type == InputType.BOOLEAN and isinstance(value, bool):
                valid_type = True
            elif (
                expected_type == InputType.LIST
                and isinstance(value, list)
                and all(isinstance(item, str) for item in value)
            ):
                valid_type = True  # Basic check for list of strings
            elif expected_type == InputType.DATE and isinstance(
                value, str
            ):  # Basic check, could add date format validation
                valid_type = True
            elif expected_type == InputType.FILE and isinstance(
                value, str
            ):  # Expecting path as string
                valid_type = True
            elif expected_type == InputType.DIRECTORY and isinstance(
                value, str
            ):  # Expecting path as string
                valid_type = True

            if not valid_type:
                raise TypeError(
                    f"Input '{input_name}' expects type {expected_type.value}, but got {type(value).__name__} for value: {value}"
                )
            final_inputs[input_name] = value
        elif default_value is not None:
            # Use default value (Pydantic should have already type-checked default_value on Workflow load)
            final_inputs[input_name] = default_value
        else:
            raise ValueError(
                f"Required input '{input_name}' (type: {expected_type.value}) was not provided and has no default value."
            )

    return final_inputs
