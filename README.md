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

This will use Nox for dependency isolation and print to stdout.
