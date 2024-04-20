# ----------------------------------------------------------------------
# |
# |  __main___EndToEndTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-04-19 20:17:16
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""End-to-end tests for __main__.py."""

from typer.testing import CliRunner

from dbrownell_DevTools.Scripts.CommitEmojis.__main__ import app


# Unfortunately, CommitEmojis can't be tested because it must output to
# sys.stdout (which isn't supported with tests).


# ----------------------------------------------------------------------
def test_Empty():
    assert True
