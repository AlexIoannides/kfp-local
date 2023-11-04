"""Testing KubeFlow Pipelines."""
from kfp import compiler, dsl

PIPELINE_ROOT_PATH = "gs://object-storage"


@dsl.component(
    packages_to_install=["numpy"],
    base_image="python:3.9",
)
def stage_0() -> None:
    """Stage 0."""
    from numpy.random import standard_normal

    x = standard_normal(100)
    print(x.mean())


@dsl.component(
    packages_to_install=["numpy"],
    base_image="python:3.9",
)
def stage_1(n: int, values: dsl.Output[dsl.Dataset]) -> None:
    """Stage 1."""
    from numpy.random import standard_normal

    x = standard_normal(n)
    with open(values.path, "w") as file:
        x.tofile(file)


@dsl.component(
    packages_to_install=["numpy"],
    base_image="python:3.9",
)
def stage_2(values: dsl.Input[dsl.Dataset]) -> None:
    """Stage 2."""
    import numpy as np

    x = np.fromfile(values.path)
    average = x.mean()
    print(average)


@dsl.pipeline(name="foo_then_bar", pipeline_root=PIPELINE_ROOT_PATH)
def pipeline(project_id: str = "42") -> None:
    """Train and deploy pipeline definition."""
    stage_0()
    data = stage_1(n=10000)
    stage_2(values=data.outputs["values"])


# example step used to create build artefacts in CI/CD pipeline
if __name__ == "__main__":
    compiler.Compiler().compile(pipeline_func=pipeline, package_path="pipeline.json", )
