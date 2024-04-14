# ----------------------------------------------------------------------
# |
# |  Output2Markdown.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-03-15 09:46:17
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Converts console output to markdown."""

import sys
import textwrap

from io import StringIO
from typing import Annotated

import typer

from ansi2html.converter import Ansi2HTMLConverter
from dbrownell_Common import SubprocessEx  # type: ignore[import-untyped]
from dbrownell_Common.Streams.Capabilities import Capabilities as StreamCapabilities  # type: ignore[import-untyped]
from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags  # type: ignore[import-untyped]
from dbrownell_Common.Streams.StreamDecorator import StreamDecorator  # type: ignore[import-untyped]
from typer.core import TyperGroup


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):
    # pylint: disable=missing-class-docstring
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs):  # pylint: disable=unused-argument
        return self.commands.keys()  # pragma: no cover


# ----------------------------------------------------------------------
app = typer.Typer(
    cls=NaturalOrderGrouper,
    help=__doc__,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
)


# ----------------------------------------------------------------------
@app.command(
    "Execute",
    help=__doc__,
    no_args_is_help=False,
)
def Execute(
    command_line: Annotated[str, typer.Argument(help="The command to execute.")],
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Write verbose information to the terminal.")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Write debug information to the terminal.")
    ] = False,
) -> None:
    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        with dm.Nested(
            "Running command line...",
            suffix="\n",
        ) as running_dm:
            sink = StreamCapabilities.Set(
                StringIO(),
                StreamCapabilities.Get(sys.stdout).Clone(
                    is_headless=True,
                    is_interactive=False,
                ),
            )

            with running_dm.YieldStream() as stdout:
                running_dm.result = SubprocessEx.Stream(
                    command_line,
                    StreamDecorator([stdout, sink]),
                )

        with dm.Nested("Converting to markdown..."):
            result = (
                Ansi2HTMLConverter(
                    inline=True,
                    line_wrap=False,
                    linkify=True,
                )
                .convert(
                    sink.getvalue(),  # type: ignore
                    full=False,
                )
                .rstrip()
            )

            # Strip the lines and add <br/> where necessary
            lines = result.split("\n")

            for index, line in enumerate(lines):
                line = line.rstrip()

                if not line:
                    line = "&nbsp;"

                lines[index] = line

            # Surround with <pre> tags
            content = """<pre style="background-color: black; color: #AAAAAA; font-size: .75em">{}</pre>""".format(
                "\n".join(lines),
            )

        dm.WriteLine(
            textwrap.dedent(
                """\


                BEGIN MARKDOWN
                --------------
                {}
                --------------
                END MARKDOWN


                """,
            ).format(content),
        )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()  # pragma: no cover
