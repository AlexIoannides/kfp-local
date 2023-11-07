"""Isolated KFP stage execution using Nox."""
import nox


@nox.session()
def run_stage(session: nox.Session):
    """Run stage by passing command and args as nox posargs"""
    session.install("kfp==2.4.0")
    file_to_edit = ".nox/run_stage/lib/python3.10/site-packages/kfp/dsl/types/artifact_types.py"
    session.run("sed", "-i", ".bak", "s/\/gcs\///", file_to_edit, external=True)
    session.run(*session.posargs, external=True)
