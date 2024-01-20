"""Compile a KubeFlow Pipeline to use for testing."""
from kfp import compiler, dsl

PIPELINE_ROOT_PATH = "gs://object-storage"


@dsl.component(
    packages_to_install=["numpy"],
    base_image="python:3.9",
)
def stage_0(config: dict, messages: list, run_id: str = "42") -> int:
    """Stage 0."""
    from numpy import random

    print(f"RUN_ID = {run_id}")
    for n, msg in enumerate(messages):
        print(f"|- message-{n}: {msg}")
    return random.randint(config["seed_low"], config["seed_high"])


@dsl.component(
    packages_to_install=["numpy"],
    base_image="python:3.9",
)
def stage_1(n: int, data: dsl.Output[dsl.Dataset], seed: int) -> None:
    """Stage 1."""
    from numpy import random

    random.seed(seed)
    x = random.standard_normal(n)
    with open(data.path, "w") as file:
        x.tofile(file)


@dsl.component(
    packages_to_install=["numpy"],
    base_image="python:3.9",
)
def stage_2(data: dsl.Input[dsl.Dataset]) -> dict:
    """Stage 2."""
    import numpy as np

    x = np.fromfile(data.path)
    return {"average": x.mean(), "std": x.std()}


@dsl.component(
    packages_to_install=["numpy"],
    base_image="python:3.9",
)
def stage_3(aggs: dict) -> None:
    """Stage 3."""
    print(f"x_average={aggs['average']}")
    print(f"x_std={aggs['std']}")


@dsl.pipeline(name="foo_then_bar", pipeline_root=PIPELINE_ROOT_PATH)
def pipeline(
    config: dict = {"seed_low": 0, "seed_high": 42},
    messages: list = ["foo", "bar"],
    run_id: str = "001",
) -> None:
    """Train and deploy pipeline definition."""
    num_obs = 1000
    stage_0_task = stage_0(config=config, messages=messages, run_id=run_id)
    stage_1_task = stage_1(n=num_obs, seed=stage_0_task.output)
    stage_2_task = stage_2(data=stage_1_task.outputs["data"])
    stage_3(aggs=stage_2_task.output)


# example step used to create build artefacts in CI/CD pipeline
if __name__ == "__main__":
    compiler.Compiler().compile(pipeline_func=pipeline, package_path="pipeline.json")
