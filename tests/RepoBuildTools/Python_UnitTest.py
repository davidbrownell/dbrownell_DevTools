# ----------------------------------------------------------------------
# |
# |  Python_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-01-21 14:14:37
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Unit tests for dbrownell_DevTools.RepoBuildTools.Python.py."""

from pathlib import Path
from typing import Any
from unittest.mock import patch

import typer

from dbrownell_DevTools.RepoBuildTools.Python import *
from typer.testing import CliRunner


# ----------------------------------------------------------------------
def test_Black():
    app = typer.Typer()

    BlackFuncFactory(Path.cwd(), app)

    result, args, kwargs = _PatchFunction(
        "Black",
        app,
        [],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 2
    assert args[1] == Path.cwd()
    assert len(kwargs) == 2
    assert kwargs["format_sources"] == False
    assert kwargs["args"] is None


# ----------------------------------------------------------------------
def test_BlackWithArgs():
    app = typer.Typer()

    BlackFuncFactory(Path.cwd(), app, "1 2 3")

    result, args, kwargs = _PatchFunction(
        "Black",
        app,
        ["--args", "four five six"],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 2
    assert args[1] == Path.cwd()
    assert len(kwargs) == 2
    assert kwargs["format_sources"] == False
    assert kwargs["args"] == "1 2 3 four five six"


# ----------------------------------------------------------------------
def test_Pylint():
    app = typer.Typer()

    PylintFuncFactory(Path.cwd(), app, 10.0)

    result, args, kwargs = _PatchFunction(
        "Pylint",
        app,
        [],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 3
    assert args[1] == Path.cwd()
    assert args[2] == 10.0
    assert len(kwargs) == 1
    assert kwargs["args"] is None


# ----------------------------------------------------------------------
def test_PylintWithArgs():
    app = typer.Typer()

    PylintFuncFactory(Path.cwd(), app, 10.0, "1 2 3")

    result, args, kwargs = _PatchFunction(
        "Pylint",
        app,
        ["--args", "four five six"],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 3
    assert args[1] == Path.cwd()
    assert args[2] == 10.0
    assert len(kwargs) == 1
    assert kwargs["args"] == "1 2 3 four five six"


# ----------------------------------------------------------------------
def test_Pytest():
    app = typer.Typer()

    PytestFuncFactory(Path.cwd(), "foo", app)

    result, args, kwargs = _PatchFunction(
        "Pytest",
        app,
        [],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 4
    assert args[1] == Path.cwd()
    assert args[2] == "foo"
    assert args[3] is None  # min_coverage
    assert len(kwargs) == 3
    assert kwargs["code_coverage"] is False
    assert kwargs["run_benchmarks"] is False
    assert kwargs["args"] is None


# ----------------------------------------------------------------------
def test_PytestWithArgs():
    app = typer.Typer()

    PytestFuncFactory(Path.cwd(), "foo", app, additional_args="1 2 3")

    result, args, kwargs = _PatchFunction(
        "Pytest",
        app,
        ["--args", "four five six"],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 4
    assert args[1] == Path.cwd()
    assert args[2] == "foo"
    assert args[3] is None  # min_coverage
    assert len(kwargs) == 3
    assert kwargs["code_coverage"] is False
    assert kwargs["run_benchmarks"] is False
    assert kwargs["args"] == "1 2 3 four five six"


# ----------------------------------------------------------------------
def test_UpdateVersion():
    app = typer.Typer()

    UpdateVersionFuncFactory(Path(__file__).parent, Path(__file__), app)

    result, args, kwargs = _PatchFunction(
        "UpdateVersion",
        app,
        [],
        "BuildActivities",
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 4
    assert args[1] == Path(__file__).parent
    assert args[2] == Path(__file__)
    assert not kwargs


# ----------------------------------------------------------------------
def test_Package():
    app = typer.Typer()

    PackageFuncFactory(Path.cwd(), app)

    result, args, kwargs = _PatchFunction(
        "Package",
        app,
        [],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 2
    assert args[1] == Path.cwd()
    assert len(kwargs) == 1
    assert kwargs["args"] is None


# ----------------------------------------------------------------------
def test_PackageWithArgs():
    app = typer.Typer()

    PackageFuncFactory(Path.cwd(), app, "1 2 3")

    result, args, kwargs = _PatchFunction(
        "Package",
        app,
        ["--args", "four five six"],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 2
    assert args[1] == Path.cwd()
    assert len(kwargs) == 1
    assert kwargs["args"] == "1 2 3 four five six"


# ----------------------------------------------------------------------
def test_Publish():
    app = typer.Typer()

    PublishFuncFactory(Path.cwd(), app)

    result, args, kwargs = _PatchFunction(
        "Publish",
        app,
        ["<token>"],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 3
    assert args[1] == Path.cwd()
    assert args[2] == "<token>"
    assert len(kwargs) == 2
    assert kwargs["production"] is False
    assert kwargs["args"] is None


# ----------------------------------------------------------------------
def test_PublishWithArgs():
    app = typer.Typer()

    PublishFuncFactory(Path.cwd(), app, "1 2 3")

    result, args, kwargs = _PatchFunction(
        "Publish",
        app,
        ["<token>", "--args", "four five six"],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 3
    assert args[1] == Path.cwd()
    assert args[2] == "<token>"
    assert len(kwargs) == 2
    assert kwargs["production"] is False
    assert kwargs["args"] == "1 2 3 four five six"


# ----------------------------------------------------------------------
def test_BuildBinary():
    app = typer.Typer()

    build_binary_filename = Path.cwd() / "build_binary.py"

    BuildBinaryFuncFactory(Path.cwd(), build_binary_filename, app)

    result, args, kwargs = _PatchFunction(
        "BuildBinary",
        app,
        [],
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 3
    assert args[1] == build_binary_filename
    assert args[2] == Path.cwd() / "build"
    assert not kwargs


# ----------------------------------------------------------------------
def test_BuildBinaries():
    app = typer.Typer()

    BuildBinariesFuncFactory(
        Path.cwd(),
        {
            "one": Path.cwd() / "one.py",
            "two": Path.cwd() / "two.py",
        },
        app,
    )

    with patch(
        "dbrownell_DevTools.RepoBuildTools.Python.PythonBuildActivities.BuildBinary",
    ) as mock:
        result = CliRunner().invoke(app, [])

    assert result.exit_code == 0
    assert result.stdout == ""

    assert len(mock.call_args_list) == 2

    # one.py
    assert len(mock.call_args_list[0].args) == 3
    assert mock.call_args_list[0].args[1] == Path.cwd() / "one.py"
    assert mock.call_args_list[0].args[2] == Path.cwd() / "build" / "one"
    assert not mock.call_args_list[0].kwargs

    # two.py
    assert len(mock.call_args_list[1].args) == 3
    assert mock.call_args_list[1].args[1] == Path.cwd() / "two.py"
    assert mock.call_args_list[1].args[2] == Path.cwd() / "build" / "two"
    assert not mock.call_args_list[1].kwargs


# ----------------------------------------------------------------------
def test_CreateDockerImage():
    app = typer.Typer()

    CreateDockerImageFuncFactory(Path.cwd(), app, "MIT")

    result, args, kwargs = _PatchFunction(
        "CreateDockerImage",
        app,
        [
            "--bootstrap-args",
            "foo",
            "--description",
            "the_description",
            "--name-suffix",
            "the_name_suffix",
        ],
        "BuildActivities",
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert len(args) == 7
    assert args[1] == Path.cwd()
    assert args[2] is None  # create_base_image_func
    assert args[3] == "--package foo"
    assert args[4] == "the_name_suffix"
    assert args[5] == "MIT"
    assert args[6] == "the_description"
    assert not kwargs


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _PatchFunction(
    function_name: str,
    app: typer.Typer,
    args: list[str],
    module_name: str = "PythonBuildActivities",
) -> tuple[Any, list[str], dict[str, str]]:
    with patch(
        f"dbrownell_DevTools.RepoBuildTools.Python.{module_name}.{function_name}",
    ) as mock:
        result = CliRunner().invoke(app, args)

        return result, mock.call_args.args, mock.call_args.kwargs
