"""Demonstrating how KFP can be used to work with compied pipelines."""
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Protocol

from google.protobuf.json_format import ParseDict, ParseError
from kfp.dsl import structures
from kfp.pipeline_spec.pipeline_spec_pb2 import PipelineSpec
from kfp.dsl.types.type_utils import (
    NUMBER_DOUBLE,
    NUMBER_INTEGER,
    BOOLEAN,
    STRING,
    LIST,
    STRUCT
)

LOCAL_FOLDER = "object-storage-bucket"
OUTPUT_METADATA_FILE = "output_metadata.json"
SCHEMA_VERSION = "2.1.0"


class _HasTypeValueAttr(Protocol):
    """Protocol definition for object with type-based access."""

    number_value: float
    bool_value: bool
    string_value: str
    list_value: list[float | bool | str]
    struct_value: dict[str, Any]


_ParamType = int | float | str | bool | list | dict


def load_pipeline_spec(compiled_pipeline_file: str) -> PipelineSpec:
    """Load compiled pipeline and parse into PipelineSpec object."""
    pipeline_file = Path.cwd() / compiled_pipeline_file
    if not pipeline_file.exists():
        raise FileNotFoundError(f"Can't find {pipeline_file}")
    component_dict = structures.load_documents_from_yaml(pipeline_file.read_text())[0]
    try:
        pipeline_spec = ParseDict(component_dict, PipelineSpec())
    except ParseError:
        raise RuntimeError(f"{pipeline_file} is not a valid `PipelineSpec`")
    return pipeline_spec


def get_task_cmd_args(name: str, pipeline: PipelineSpec) -> tuple[list[str], list[str]]:
    """Return the requested task execution commands."""
    executor_name = f"exec-{name}"
    executors = pipeline.deployment_spec.fields["executors"].struct_value.fields
    if executor_name not in executors:
        raise ValueError(f"{name} not found in pipeline")
    task = executors[f"exec-{name}"].struct_value.fields["container"].struct_value.fields
    cmd = [cmd for cmd in task["command"].list_value]
    args = [arg for arg in task["args"].list_value]
    return cmd, args


def _extract_value(param_obj: _HasTypeValueAttr, param_type: int) -> _ParamType:
    """Extract parameer value based on type."""
    if param_type == NUMBER_INTEGER:
        return int(param_obj.number_value)
    elif param_type == NUMBER_DOUBLE:
        return float(param_obj.number_value)
    elif param_type == BOOLEAN:
        return bool(param_obj.bool_value)
    elif param_type == STRING:
        return str(param_obj.string_value)
    elif param_type == LIST:
        return [e for e in param_obj.list_value]
    elif param_type == STRUCT:
        return dict(param_obj.struct_value)
    else:
        raise RuntimeError("parameter has an unknown type.")


def _get_param_value_from_metadata_file(
        task_name: str, output_key: str = "Output"
    ) -> _ParamType:
    """Get output parameter from output_metadata.json file."""
    output_metadata_file = Path.cwd() / LOCAL_FOLDER / task_name / OUTPUT_METADATA_FILE
    if not output_metadata_file.exists():
        raise FileNotFoundError(f"couldn't find {output_metadata_file}")
    output_metadata = json.loads(output_metadata_file.read_text())
    try:
        output_value = output_metadata["parameterValues"][output_key]
    except KeyError:
        raise RuntimeError(f"couldn't find parameter output for task={task_name}")
    return output_value


def _get_param_value_from_pipeline_inputs(
        pipeline: PipelineSpec, param_name: str
    ) -> _ParamType:
    """Get pipeline input."""
    pipeline_inputs = pipeline.root.input_definitions.parameters
    try:
        param =  pipeline_inputs[param_name]
    except KeyError:
        raise RuntimeError("couldn't find parameter in pipeline inputs")
    return _extract_value(param.default_value, param.parameter_type)


def _get_param_value(
        pipeline: PipelineSpec, task_name: str, param_name: str
    ) -> _ParamType:
    """Find parameter value for a task."""
    try:
        component_name = f"comp-{task_name}"
        component = pipeline.components[component_name]
        task = pipeline.root.dag.tasks[task_name]
    except KeyError:
        RuntimeError(f"{task_name} is not a task in the pipeline specification")

    try:
        param_type = component.input_definitions.parameters[param_name].parameter_type
        param = task.inputs.parameters[param_name]
    except KeyError:
        raise RuntimeError(f"Cannot find param={param_name} in task={task_name}")

    if str(param.runtime_value):
        return _extract_value(param.runtime_value.constant, param_type)
    elif str(param.task_output_parameter):
        return _get_param_value_from_metadata_file(
            param.task_output_parameter.producer_task,
            param.task_output_parameter.output_parameter_key
        )
    elif str(param.component_input_parameter):
        return _get_param_value_from_pipeline_inputs(
            pipeline, param.component_input_parameter
        )
    else:
        if str(component.input_definitions.parameters[param_name].default_value):
            param = component.input_definitions.parameters[param_name]
            return _extract_value(param.default_value, param_type)
        raise RuntimeError(f"Unsupported parameter type in task {task_name}")


def get_func_args(pipeline: PipelineSpec, task_name: str) -> str:
    component_name = f"comp-{task_name}"
    component = pipeline.components[component_name]
    input_parameters = [param for param in component.input_definitions.parameters]
    input_artifacts = [artifact for artifact in component.input_definitions.artifacts]
    output_artifacts = [artifact for artifact in component.output_definitions.artifacts]

    input_params_spec: dict[str, Any] = {}
    for param in input_parameters:
        input_params_spec[param] = _get_param_value(pipeline, task_name, param)

    input_artifacts_spec: dict[str, Any] = {}
    for artifact in input_artifacts:
        uri = f"gs://{LOCAL_FOLDER}/{artifact}"
        input_artifacts_spec[artifact] = {"name": artifact, "artifacts": [{"uri": uri}]}

    output_artifacts_spec: dict[str, Any] = {}
    for artifact in output_artifacts:
        uri = f"gs://{LOCAL_FOLDER}/{artifact}"
        output_artifacts_spec[artifact] = {
            "artifacts": [{"name": artifact, "uri": uri}]
        }

    executor_args = {
        "inputs": {
            "parameterValues": input_params_spec,
            "artifacts": input_artifacts_spec
        },
        "outputs": {
            "artifacts": output_artifacts_spec,
            "outputFile": f"{LOCAL_FOLDER}/{task_name}/output_metadata.json"
        }
    }
    return json.dumps(executor_args)


def run_pipeline(
        compiled_pipeline_json: str = "pipeline.json", use_nox: bool = True
    ) -> None:
    """Run a compiled pipeline with default parameter values."""
    pipeline = load_pipeline_spec(compiled_pipeline_json)
    if pipeline.schema_version != SCHEMA_VERSION:
        msg = (
            f"schema_version={pipeline.schema_version} not supported - please revert to"
            " schema_version={SCHEMA_VERSION} "
        )
        raise RuntimeError(msg)
    shutil.rmtree(LOCAL_FOLDER, ignore_errors=True)
    for task in pipeline.root.dag.tasks:
        cmd, args = get_task_cmd_args(task, pipeline)
        args[1] = get_func_args(pipeline, task)
        if use_nox:
            subprocess.run(["nox", "-s", "run_pipeline_task", "--", *(cmd + args)])
        else:
            subprocess.run(cmd + args)


if __name__ == "__main__":
    run_pipeline()
