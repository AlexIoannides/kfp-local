"""Isolated KFP stage execution using Nox."""
import nox

KFP_VERSION = "2.4.0"
KFP_MODULE_EDIT = (
    ".nox/run_pipeline_task/lib/python3.10/site-packages/"
    "kfp/dsl/types/artifact_types.py"
)


@nox.session()
def run_pipeline_task(session: nox.Session):
    """Run stage by passing command and args as nox posargs."""
    session.chdir(session.invoked_from)
    session.install(f"kfp=={KFP_VERSION}")
    session.run("sed", "-i", ".bak", r"s/\/gcs\///", KFP_MODULE_EDIT, external=True)
    session.run(*session.posargs, external=True)
