# ----------------------------------------------------------------------
# |
# |  update_data.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-11-01 09:59:32
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022-23
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Updates the Gitmoji data"""

from pathlib import Path
from typing import Annotated

import requests  # type: ignore[import-untyped]
import typer

from typer.core import TyperGroup

from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags  # type: ignore[import-untyped]


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs):  # pylint: disable=unused-argument
        return self.commands.keys()


# ----------------------------------------------------------------------
app = typer.Typer(
    cls=NaturalOrderGrouper,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
)


# ----------------------------------------------------------------------
@app.command("Update", no_args_is_help=False)
def Update(  # pylint: disable=dangerous-default-value
    url_base: Annotated[
        str, typer.Option("--url-base", help="Base url of the gitmoji data.")
    ] = "https://raw.githubusercontent.com/carloscuesta/gitmoji/master/packages/gitmojis/src",
    filenames: Annotated[
        list[str], typer.Option("--filename", help="gitmoji files to download.")
    ] = ["gitmojis.json", "schema.json"],
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Write verbose information to the terminal.")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Write debug information to the terminal.")
    ] = False,
) -> None:
    """Updates the Gitmoji data."""

    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        this_dir = Path(__file__).parent

        for filename_index, filename in enumerate(filenames):
            with dm.Nested(
                "Downloading '{}' ({} of {})...".format(
                    filename,
                    filename_index + 1,
                    len(filenames),
                ),
            ):
                response = requests.get(  # pylint: disable=missing-timeout
                    "{}/{}".format(url_base, filename)
                )
                response.raise_for_status()

                content = response.text

                with (this_dir / filename).open(
                    "w",
                    encoding="UTF-8",
                ) as f:
                    f.write(content)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
