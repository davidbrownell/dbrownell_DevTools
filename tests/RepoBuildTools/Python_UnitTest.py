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
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
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


# ----------------------------------------------------------------------
def test_UpdateVersion():
    app = typer.Typer()

    UpdateVersionFuncFactory(_python_tests_dir, app)


# ----------------------------------------------------------------------
def test_Package():
    app = typer.Typer()

    PackageFuncFactory(_python_tests_dir, app)


# ----------------------------------------------------------------------
def test_Publish():
    app = typer.Typer()

    PublishFuncFactory(_python_tests_dir, app)
