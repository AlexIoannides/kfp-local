"""Basic tests for run_pipeline module."""
import json
import shutil
from pathlib import Path
from typing import Any
from unittest.mock import patch

from kfp.dsl.types.type_utils import (
    BOOLEAN,
    LIST,
    NUMBER_DOUBLE,
    NUMBER_INTEGER,
    STRING,
    STRUCT,
)
from kfp.pipeline_spec.pipeline_spec_pb2 import PipelineSpec
from pytest import fixture, mark, raises

from kfp_local.run_pipeline import (
    LOCAL_FOLDER,
    _extract_value,
    _get_param_value,
    _get_param_value_from_metadata_file,
    _get_param_value_from_pipeline_inputs,
    get_func_args,
    get_task_cmd_args,
    load_pipeline_spec,
    run_pipeline,
)

TEST_CONFIG_FILE = "tests/resources/pipeline.json"


@fixture(scope="function")
def pipeline_spec() -> PipelineSpec:
    return load_pipeline_spec(TEST_CONFIG_FILE)


@fixture(scope="function")
def pipeline_spec_dict() -> dict[str, Any]:
    test_config_file = Path(TEST_CONFIG_FILE)
    return json.loads(test_config_file.read_text())["deploymentSpec"]


def test_load_pipeline_spec_loads_valid_config_files():
    assert type(load_pipeline_spec(TEST_CONFIG_FILE)) is PipelineSpec


def test_load_pipeline_spec_raises_error_if_config_file_not_found():
    with raises(FileNotFoundError, match="Can't find"):
        load_pipeline_spec("NOT_A_FILE.json")


def test_load_pipeline_spec_raises_error_if_config_file_invalid():
    with raises(RuntimeError, match="not a valid `PipelineSpec`"):
        load_pipeline_spec("README.md")


def test_get_task_cmd_args_return_the_right_args(
    pipeline_spec: PipelineSpec, pipeline_spec_dict: dict[str, Any]
):
    stage = "stage-0"
    stage_spec = pipeline_spec_dict["executors"][f"exec-{stage}"]["container"]
    expected_cmd = stage_spec["command"]
    expected_args = stage_spec["args"]
    cmd, args = get_task_cmd_args(stage, pipeline_spec)
    assert cmd == expected_cmd
    assert args == expected_args


def test_get_task_cmd_args_raises_error_if_task_not_found(pipeline_spec: PipelineSpec):
    with raises(ValueError, match="not found in pipeline"):
        get_task_cmd_args("THIS_TASK_DOES_NOT_EXIST", pipeline_spec)


@mark.parametrize(
    ["param_type", "expected_type"],
    [
        (NUMBER_INTEGER, int),
        (NUMBER_DOUBLE, float),
        (BOOLEAN, bool),
        (STRING, str),
        (LIST, list),
        (STRUCT, dict),
    ],
)
def test_extract_value(param_type, expected_type):
    class TestParamObj:
        number_value = 42.5
        bool_value = False
        string_value = "foo"
        list_value = (1, 2, 3)
        struct_value = {"a": 1, "b": 2}

    assert type(_extract_value(TestParamObj(), param_type)) == expected_type


def test_get_param_value_from_metadata_file_returns_correct_values():
    with patch("kfp_local.run_pipeline.LOCAL_FOLDER", new="tests/resources"):
        param = _get_param_value_from_metadata_file("stage-0")
    assert param == 42


def test_get_param_value_from_metadata_raises_error_when_file_not_found():
    with patch("kfp_local.run_pipeline.LOCAL_FOLDER", new="DOES_NOT_EXIST"):
        with raises(FileNotFoundError, match="couldn't find"):
            _get_param_value_from_metadata_file("stage-0")


def test_get_param_value_from_metadata_raises_error_key_not_found():
    with patch("kfp_local.run_pipeline.LOCAL_FOLDER", new="tests/resources"):
        with raises(RuntimeError, match="couldn't find"):
            _get_param_value_from_metadata_file("stage-0", output_key="DONT_EXIST")


def test_get_param_value_from_pipeline_inputs_raises_error_if_param_not_found(
    pipeline_spec: PipelineSpec,
):
    with raises(RuntimeError, match="couldn't find parameter"):
        _get_param_value_from_pipeline_inputs(pipeline_spec, "DOES_NOT_EXIST")


def test_get_param_value_raises_error_if_task_not_in_pipeline_spec(
    pipeline_spec: PipelineSpec,
):
    bad_task_name = "foo"
    with raises(RuntimeError, match=f"{bad_task_name} is not a task in the pipeline"):
        _get_param_value(pipeline_spec, bad_task_name, "the_param")


def test_get_param_value_raises_error_if_param_not_in_task_spec(
    pipeline_spec: PipelineSpec,
):
    bad_param_name = "foo"
    with raises(RuntimeError, match=f"Cannot find param={bad_param_name}"):
        _get_param_value(pipeline_spec, "stage-1", bad_param_name)


def test_get_param_value_raises_finds_parameters(pipeline_spec: PipelineSpec):
    assert _get_param_value(pipeline_spec, "stage-0", "run_id") == "001"
    assert _get_param_value(pipeline_spec, "stage-1", "n") == 1000

    with patch("kfp_local.run_pipeline.LOCAL_FOLDER", new="tests/resources"):
        assert _get_param_value(pipeline_spec, "stage-1", "seed") == 42


def test_get_func_args(pipeline_spec: PipelineSpec):
    s0_args_expected = {
        "inputs": {
            "artifacts": {},
            "parameterValues": {
                "config": {"seed_high": 42.0, "seed_low": 0.0},
                "messages": ["foo", "bar"],
                "run_id": "001",
            },
        },
        "outputs": {
            "artifacts": {},
            "outputFile": "object-storage-bucket/stage-0/output_metadata.json",
        },
    }
    s0_args = json.loads(get_func_args(pipeline_spec, "stage-0"))
    assert s0_args == s0_args_expected

    s1_args_expected = {
        "inputs": {"parameterValues": {"n": 1000, "seed": 42}, "artifacts": {}},
        "outputs": {
            "artifacts": {
                "data": {
                    "artifacts": [{"name": "data", "uri": "gs://tests/resources/data"}]
                }
            },
            "outputFile": "tests/resources/stage-1/output_metadata.json",
        },
    }
    with patch("kfp_local.run_pipeline.LOCAL_FOLDER", new="tests/resources"):
        s1_args = json.loads(get_func_args(pipeline_spec, "stage-1"))
    assert s1_args == s1_args_expected

    s2_args_expected = {
        "inputs": {
            "parameterValues": {},
            "artifacts": {
                "data": {
                    "name": "data",
                    "artifacts": [{"uri": "gs://tests/resources/data"}],
                }
            },
        },
        "outputs": {
            "artifacts": {},
            "outputFile": "tests/resources/stage-2/output_metadata.json",
        },
    }
    with patch("kfp_local.run_pipeline.LOCAL_FOLDER", new="tests/resources"):
        s2_args = json.loads(get_func_args(pipeline_spec, "stage-2"))
    assert s2_args == s2_args_expected


def test_run_pipeline_raises_error_if_pipeline_spec_schema_version_mismatch():
    with patch("kfp_local.run_pipeline.SCHEMA_VERSION", new="3.1.0"):
        with raises(RuntimeError, match="schema_version=2.1.0 not supported"):
            run_pipeline(["some-stage"], TEST_CONFIG_FILE)


def test_run_pipeline_raises_error_if_task_def_missing_from_pipeline_spec():
    with raises(RuntimeError, match="missing task defs in pipeline spec: some-stage"):
        run_pipeline(["some-stage"], TEST_CONFIG_FILE)


def test_run_pipeline_raises_error_if_task_execution_fails():
    with patch("kfp_local.run_pipeline.get_func_args") as mock_get_func_args:
        mock_get_func_args.side_effect = Exception()
        with raises(RuntimeError, match="task=stage-0 failed to execute"):
            run_pipeline(["stage-0"], TEST_CONFIG_FILE)


def test_run_pipeline_end_to_end_with_dev_venv():
    dag = ["stage-0", "stage-1", "stage-2", "stage-3"]
    try:
        run_pipeline(dag, TEST_CONFIG_FILE, use_nox=False)
        final_stage_output = Path(LOCAL_FOLDER) / "stage-3" / "output_metadata.json"
        assert final_stage_output.exists()
    except Exception:
        assert False
    finally:
        shutil.rmtree(LOCAL_FOLDER, ignore_errors=True)


def test_run_pipeline_end_to_end_with_nox():
    dag = ["stage-0", "stage-1", "stage-2", "stage-3"]
    try:
        run_pipeline(dag, TEST_CONFIG_FILE, use_nox=True)
        final_stage_output = Path(LOCAL_FOLDER) / "stage-3" / "output_metadata.json"
        assert final_stage_output.exists()
    except Exception:
        assert False
    finally:
        shutil.rmtree(LOCAL_FOLDER, ignore_errors=True)
