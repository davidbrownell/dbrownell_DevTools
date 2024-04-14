# ----------------------------------------------------------------------
# |
# |  Output2Markdown_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-03-15 10:38:22
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
# """Unit tests for Output2Markdown.py."""


from dbrownell_DevTools.Scripts.Output2Markdown import app
from typer.testing import CliRunner


# ----------------------------------------------------------------------
def test_SingleLine():
    result = CliRunner().invoke(app, ['''python -c \"print('Hello world!')\"'''])

    assert result.exit_code == 0
    assert result.stdout == ""
