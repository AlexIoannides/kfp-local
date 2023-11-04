"""Demonstrating how KFP can be used to work with compied pipelines."""
import json
import subprocess
from pathlib import Path

from google.protobuf.json_format import ParseDict, ParseError
from kfp.dsl import structures
from kfp.pipeline_spec.pipeline_spec_pb2 import PipelineSpec


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


def get_stage_cmd_args(name: str, pipeline: PipelineSpec) -> tuple[list[str], list[str]]:
    """Return the requested stage."""
    executor_name = f"exec-{name}"
    executors = pipeline.deployment_spec.fields["executors"].struct_value.fields
    if executor_name not in executors:
        raise ValueError(f"{name} not found in pipeline")
    stage = executors[f"exec-{name}"].struct_value.fields["container"].struct_value.fields
    cmd = [cmd for cmd in stage["command"].list_value]
    args = [arg for arg in stage["args"].list_value]
    return cmd, args


def executor_input(stage: str) -> str:
    """Get executor input."""
    executor_inputs = {
        "stage-0": {
            "inputs": {},
            "outputs": {
                "outputFile": "object-storage/metadata.json"
            }
        },
        "stage-1": {
            "inputs": {
                "parameterValues": {
                    "n": 100
                },
            },
            "outputs": {
                "artifacts": {
                    "values": {
                        "artifacts": [
                            {
                                "type": {"schemaTitle": "google.VertexDataset"},
                                "uri": "gs://object-storage/values"
                            }
                        ]
                    }
                },
                "outputFile": "object-storage/metadata.json"
            }
        },
        "stage-2": {
            "inputs": {
                "artifacts": {
                    "values": {
                        "artifacts": [
                            {
                                "type": {"schemaTitle": "google.VertexDataset"},
                                "uri": "gs://object-storage/values"
                            }
                        ]
                    }
                }
            },
            "outputs": {
                "outputFile": "object-storage/metadata.json"
            }
        }
    }
    return(json.dumps(executor_inputs[stage]).replace('"', '\"'))

if __name__ == "__main__":
    pipeline = load_pipeline_spec("pipeline.json")
    for stage in ["stage-0", "stage-1", "stage-2"]:
        cmd, args = get_stage_cmd_args(stage, pipeline)
        args[1] = executor_input(stage)
        # subprocess.run(cmd + args)
        subprocess.run(["nox", "-s", "run_stage", "--", *(cmd + args)])
