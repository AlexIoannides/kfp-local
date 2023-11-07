# Local Pipelines for Local People

A local executor for Kubeflow pipelines componsed entirely out of custom Python components.

## Setup

```text
pip install -r requirements.txt
```

## Compile Pipeline

As defined in `make_pipeline.py`,

```text
python make_pipeline.py
```

This will produce a compiled pipeline contained in `pipeline.json`

## Run Compiled Pipeline Locally

To run the pipeline defined in `pipeline.json`,

```text
python run_pipeline.py
```

This will use Nox for dependency isolation and print to stdout. The output should look like,

```text
nox > Running session run_pipeline_task
nox > Creating virtual environment (virtualenv) using python3.10 in .nox/run_pipeline_task
nox > python -m pip install kfp==2.4.0
nox > sed -i .bak 's/\/gcs\///' .nox/run_pipeline_task/lib/python3.10/site-packages/kfp/dsl/types/artifact_types.py
nox > sh -c '
if ! [ -x "$(command -v pip)" ]; then
    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip
fi

PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet --no-warn-script-location '"'"'kfp==2.4.0'"'"' '"'"'--no-deps'"'"' '"'"'typing-extensions>=3.7.4,<5; python_version<"3.9"'"'"'  &&  python3 -m pip install --quiet --no-warn-script-location '"'"'numpy'"'"' && "$0" "$@"
' sh -ec 'program_path=$(mktemp -d)

printf "%s" "$0" > "$program_path/ephemeral_component.py"
_KFP_RUNTIME=true python3 -m kfp.dsl.executor_main                         --component_module_path                         "$program_path/ephemeral_component.py"                         "$@"
' '
import kfp
from kfp import dsl
from kfp.dsl import *
from typing import *

def stage_0(config: Dict[str, Any], messages: List[str], run_id: str = "42") -> int:
    """Stage 0."""
    from numpy import random

    print(f"RUN_ID = {run_id}")
    for n, msg in enumerate(messages):
        print(f"|- message-{n}: {msg}")
    return random.randint(config["seed_low"], config["seed_high"])

' --executor_input '{"inputs": {"parameterValues": {"config": {"seed_high": 42.0, "seed_low": 0.0}, "messages": ["foo", "bar"], "run_id": "001"}, "artifacts": {}}, "outputs": {"artifacts": {}, "outputFile": "object-storage-bucket/stage-0/output_metadata.json"}}' --function_to_execute stage_0
[KFP Executor 2023-11-07 13:21:47,199 INFO]: Looking for component `stage_0` in --component_module_path `/var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.TrHWwseBIp/ephemeral_component.py`
[KFP Executor 2023-11-07 13:21:47,199 INFO]: Loading KFP component "stage_0" from /var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.TrHWwseBIp/ephemeral_component.py (directory "/var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.TrHWwseBIp" and module name "ephemeral_component")
[KFP Executor 2023-11-07 13:21:47,200 INFO]: Got executor_input:
{
    "inputs": {
        "parameterValues": {
            "config": {
                "seed_high": 42.0,
                "seed_low": 0.0
            },
            "messages": [
                "foo",
                "bar"
            ],
            "run_id": "001"
        },
        "artifacts": {}
    },
    "outputs": {
        "artifacts": {},
        "outputFile": "object-storage-bucket/stage-0/output_metadata.json"
    }
}
RUN_ID = 001
|- message-0: foo
|- message-1: bar
[KFP Executor 2023-11-07 13:21:48,207 INFO]: Wrote executor output file to object-storage-bucket/stage-0/output_metadata.json.
nox > Session run_pipeline_task was successful.
nox > Running session run_pipeline_task
nox > Creating virtual environment (virtualenv) using python3.10 in .nox/run_pipeline_task
nox > python -m pip install kfp==2.4.0
nox > sed -i .bak 's/\/gcs\///' .nox/run_pipeline_task/lib/python3.10/site-packages/kfp/dsl/types/artifact_types.py
nox > sh -c '
if ! [ -x "$(command -v pip)" ]; then
    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip
fi

PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet --no-warn-script-location '"'"'kfp==2.4.0'"'"' '"'"'--no-deps'"'"' '"'"'typing-extensions>=3.7.4,<5; python_version<"3.9"'"'"'  &&  python3 -m pip install --quiet --no-warn-script-location '"'"'numpy'"'"' && "$0" "$@"
' sh -ec 'program_path=$(mktemp -d)

printf "%s" "$0" > "$program_path/ephemeral_component.py"
_KFP_RUNTIME=true python3 -m kfp.dsl.executor_main                         --component_module_path                         "$program_path/ephemeral_component.py"                         "$@"
' '
import kfp
from kfp import dsl
from kfp.dsl import *
from typing import *

def stage_1(n: int, data: dsl.Output[dsl.Dataset], seed: int) -> None:
    """Stage 1."""
    from numpy import random

    random.seed(seed)
    x = random.standard_normal(n)
    with open(data.path, "w") as file:
        x.tofile(file)

' --executor_input '{"inputs": {"parameterValues": {"n": 1000, "seed": 23}, "artifacts": {}}, "outputs": {"artifacts": {"data": {"artifacts": [{"name": "data", "uri": "gs://object-storage-bucket/data"}]}}, "outputFile": "object-storage-bucket/stage-1/output_metadata.json"}}' --function_to_execute stage_1
[KFP Executor 2023-11-07 13:21:55,481 INFO]: Looking for component `stage_1` in --component_module_path `/var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.YtqXEolyXe/ephemeral_component.py`
[KFP Executor 2023-11-07 13:21:55,482 INFO]: Loading KFP component "stage_1" from /var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.YtqXEolyXe/ephemeral_component.py (directory "/var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.YtqXEolyXe" and module name "ephemeral_component")
[KFP Executor 2023-11-07 13:21:55,482 INFO]: Got executor_input:
{
    "inputs": {
        "parameterValues": {
            "n": 1000,
            "seed": 23
        },
        "artifacts": {}
    },
    "outputs": {
        "artifacts": {
            "data": {
                "artifacts": [
                    {
                        "name": "data",
                        "uri": "gs://object-storage-bucket/data"
                    }
                ]
            }
        },
        "outputFile": "object-storage-bucket/stage-1/output_metadata.json"
    }
}
[KFP Executor 2023-11-07 13:21:56,218 INFO]: Wrote executor output file to object-storage-bucket/stage-1/output_metadata.json.
nox > Session run_pipeline_task was successful.
nox > Running session run_pipeline_task
nox > Creating virtual environment (virtualenv) using python3.10 in .nox/run_pipeline_task
nox > python -m pip install kfp==2.4.0
nox > sed -i .bak 's/\/gcs\///' .nox/run_pipeline_task/lib/python3.10/site-packages/kfp/dsl/types/artifact_types.py
nox > sh -c '
if ! [ -x "$(command -v pip)" ]; then
    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip
fi

PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet --no-warn-script-location '"'"'kfp==2.4.0'"'"' '"'"'--no-deps'"'"' '"'"'typing-extensions>=3.7.4,<5; python_version<"3.9"'"'"'  &&  python3 -m pip install --quiet --no-warn-script-location '"'"'numpy'"'"' && "$0" "$@"
' sh -ec 'program_path=$(mktemp -d)

printf "%s" "$0" > "$program_path/ephemeral_component.py"
_KFP_RUNTIME=true python3 -m kfp.dsl.executor_main                         --component_module_path                         "$program_path/ephemeral_component.py"                         "$@"
' '
import kfp
from kfp import dsl
from kfp.dsl import *
from typing import *

def stage_2(data: dsl.Input[dsl.Dataset]) -> Dict[str, Any]:
    """Stage 2."""
    import numpy as np

    x = np.fromfile(data.path)
    return {"average": x.mean(), "std": x.std()}

' --executor_input '{"inputs": {"parameterValues": {}, "artifacts": {"data": {"name": "data", "artifacts": [{"uri": "gs://object-storage-bucket/data"}]}}}, "outputs": {"artifacts": {}, "outputFile": "object-storage-bucket/stage-2/output_metadata.json"}}' --function_to_execute stage_2
[KFP Executor 2023-11-07 13:22:03,723 INFO]: Looking for component `stage_2` in --component_module_path `/var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.zX0TENC8H2/ephemeral_component.py`
[KFP Executor 2023-11-07 13:22:03,723 INFO]: Loading KFP component "stage_2" from /var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.zX0TENC8H2/ephemeral_component.py (directory "/var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.zX0TENC8H2" and module name "ephemeral_component")
[KFP Executor 2023-11-07 13:22:03,724 INFO]: Got executor_input:
{
    "inputs": {
        "parameterValues": {},
        "artifacts": {
            "data": {
                "name": "data",
                "artifacts": [
                    {
                        "uri": "gs://object-storage-bucket/data"
                    }
                ]
            }
        }
    },
    "outputs": {
        "artifacts": {},
        "outputFile": "object-storage-bucket/stage-2/output_metadata.json"
    }
}
[KFP Executor 2023-11-07 13:22:04,564 INFO]: Wrote executor output file to object-storage-bucket/stage-2/output_metadata.json.
nox > Session run_pipeline_task was successful.
nox > Running session run_pipeline_task
nox > Creating virtual environment (virtualenv) using python3.10 in .nox/run_pipeline_task
nox > python -m pip install kfp==2.4.0
nox > sed -i .bak 's/\/gcs\///' .nox/run_pipeline_task/lib/python3.10/site-packages/kfp/dsl/types/artifact_types.py
nox > sh -c '
if ! [ -x "$(command -v pip)" ]; then
    python3 -m ensurepip || python3 -m ensurepip --user || apt-get install python3-pip
fi

PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install --quiet --no-warn-script-location '"'"'kfp==2.4.0'"'"' '"'"'--no-deps'"'"' '"'"'typing-extensions>=3.7.4,<5; python_version<"3.9"'"'"'  &&  python3 -m pip install --quiet --no-warn-script-location '"'"'numpy'"'"' && "$0" "$@"
' sh -ec 'program_path=$(mktemp -d)

printf "%s" "$0" > "$program_path/ephemeral_component.py"
_KFP_RUNTIME=true python3 -m kfp.dsl.executor_main                         --component_module_path                         "$program_path/ephemeral_component.py"                         "$@"
' '
import kfp
from kfp import dsl
from kfp.dsl import *
from typing import *

def stage_3(aggs: Dict[str, float]) -> None:
    """Stage 3."""
    print(f"x_average={aggs['"'"'average'"'"']}")
    print(f"x_std={aggs['"'"'std'"'"']}")

' --executor_input '{"inputs": {"parameterValues": {"aggs": {"average": -0.061227051591934534, "std": 0.9617933551902902}}, "artifacts": {}}, "outputs": {"artifacts": {}, "outputFile": "object-storage-bucket/stage-3/output_metadata.json"}}' --function_to_execute stage_3
[KFP Executor 2023-11-07 13:22:12,126 INFO]: Looking for component `stage_3` in --component_module_path `/var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.ZQ68zUMrVG/ephemeral_component.py`
[KFP Executor 2023-11-07 13:22:12,126 INFO]: Loading KFP component "stage_3" from /var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.ZQ68zUMrVG/ephemeral_component.py (directory "/var/folders/xk/fqw466sd3l7fztkl08x8hnk80000gn/T/tmp.ZQ68zUMrVG" and module name "ephemeral_component")
[KFP Executor 2023-11-07 13:22:12,127 INFO]: Got executor_input:
{
    "inputs": {
        "parameterValues": {
            "aggs": {
                "average": -0.061227051591934534,
                "std": 0.9617933551902902
            }
        },
        "artifacts": {}
    },
    "outputs": {
        "artifacts": {},
        "outputFile": "object-storage-bucket/stage-3/output_metadata.json"
    }
}
x_average=-0.061227051591934534
x_std=0.9617933551902902
[KFP Executor 2023-11-07 13:22:12,127 INFO]: Wrote executor output file to object-storage-bucket/stage-3/output_metadata.json.
nox > Session run_pipeline_task was successful.
```
