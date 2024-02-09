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

import typer

from dbrownell_DevTools.RepoBuildTools.Python import *
from typer.testing import CliRunner


# ----------------------------------------------------------------------
_python_tests_dir = Path(__file__).parent / "PythonTests"


# ----------------------------------------------------------------------
def test_Black():
    app = typer.Typer()

    BlackFuncFactory(_python_tests_dir, app)

    result = CliRunner().invoke(app, [])

    assert result.exit_code == 0
    assert result.stdout == ""


# ----------------------------------------------------------------------
def test_Pylint():
    app = typer.Typer()

    PylintFuncFactory(_python_tests_dir, app, 10.0)

    result = CliRunner().invoke(app, [])

    assert result.exit_code == 0
    assert result.stdout == ""


# ----------------------------------------------------------------------
def test_Pytest():
    app = typer.Typer()

    PytestFuncFactory(_python_tests_dir, "", app)

    result = CliRunner().invoke(app, [])

    assert result.exit_code == 0
    assert result.stdout == ""


# TODO # ----------------------------------------------------------------------
# TODO def test_UpdateVersion():
# TODO     app = typer.Typer()
# TODO
# TODO     root_dir = Path(__file__).parent.parent.parent
# TODO     UpdateVersionFuncFactory(root_dir, _python_tests_dir, app)
# TODO
# TODO     result = CliRunner().invoke(app, [])
# TODO
# TODO     assert result.exit_code == 0
# TODO     assert result.stdout == ""


# ----------------------------------------------------------------------
def test_Package():
    app = typer.Typer()

    PackageFuncFactory(_python_tests_dir, app)


# ----------------------------------------------------------------------
def test_Publish():
    app = typer.Typer()

    PublishFuncFactory(_python_tests_dir, app)
