# ----------------------------------------------------------------------
# |
# |  MatchTests_EndToEndTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-04-13 23:05:44
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""End-to-end tests for MatchTests.py."""

from pathlib import Path

from dbrownell_Common import PathEx
from typer.testing import CliRunner

from dbrownell_DevTools.Scripts.Python.MatchTests import app


# ----------------------------------------------------------------------
def test_Standard():
    repo_root = PathEx.EnsureDir(Path(__file__).parent.parent.parent.parent)

    result = CliRunner().invoke(app)

    assert result.exit_code == 0, result.output
