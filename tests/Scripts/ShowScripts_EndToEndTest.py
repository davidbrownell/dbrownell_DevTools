# ----------------------------------------------------------------------
# |
# |  ShowScripts_EndToEndTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-04-13 23:50:22
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""End-to-end tests for ShowScripts.py."""

from typer.testing import CliRunner

from dbrownell_DevTools.Scripts.ShowScripts import app


# ----------------------------------------------------------------------
def test_Standard():
    result = CliRunner().invoke(app)

    assert result.exit_code == 0, result.output
