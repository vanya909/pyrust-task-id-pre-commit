"""Script to auto-release new versions of `pyrust-task-id-pre-commit`.

This script will automatically update version of `pyrust-task-id-pre-commit`
right after update of `pyrust-task-id`.

"""
import tomllib
import tomli_w
import requests
from invoke.tasks import task
from invoke.context import Context

type Version = str
type PyProject = dict


@task
def release(context: Context):
    """Bump versions.

    For all new versions of main package update the dependency version, commit
    and add new tag.

    """
    for version in get_target_versions():
        process_version(version)

        result = context.run("git status -s", hide=True)
        is_changed = result and result.stdout.strip()
        if not is_changed:
            print(f"No changes for v{version}")
            return

        commands = [
            "git add .",
            f"git commit -m \"Bump version {version}\"",
            f"git tag \"v{version}\"",
        ]

        for command in commands:
            context.run(command)


def get_target_versions() -> list[Version]:
    """Return list of versions that need to be released."""
    pyproject = get_pyproject_content()
    all_versions = get_all_versions()
    current_version = get_current_version(pyproject=pyproject)
    return [
        version
        for version in all_versions
        if version > current_version
    ]


def get_pyproject_content() -> PyProject:
    """Return content of `pyproject.toml`."""
    with open("pyproject.toml", "rb") as pyproject:
        return tomllib.load(pyproject)


def get_all_versions() -> list[Version]:
    """Return all available versions from PyPI."""
    response = requests.get("https://pypi.org/pypi/pyrust-task-id/json")
    response.raise_for_status()

    return sorted(response.json()["releases"])


def get_current_version(pyproject: dict) -> Version:
    """Return current main package's version from `pyproject.toml`"""
    return pyproject["project"]["dependencies"][0].split("==")[1]


def process_version(version: Version):
    """Update main package's version in `pyproject.toml` file."""
    main_package_name = "pyrust-task-id"

    data = get_pyproject_content()
    data["project"]["dependencies"] = [f"{main_package_name}=={version}"]

    with open("pyproject.toml", mode="wb") as pyproject:
        tomli_w.dump(data, pyproject)
