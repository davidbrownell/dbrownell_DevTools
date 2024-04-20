# ----------------------------------------------------------------------
# |
# |  __main__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-04-19 19:41:45
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Tools to create and display emojis used when committing changes to a repository."""

import json
import re
import sys
import textwrap

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Match, Optional

import typer

from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags  # type: ignore[import-untyped]
from rich.console import Console, Group
from rich.table import Table
from rich.text import Text
from typer.core import TyperGroup


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):
    # pylint: disable=missing-class-docstring
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs):  # pylint: disable=unused-argument
        return self.commands.keys()


# ----------------------------------------------------------------------
app = typer.Typer(
    cls=NaturalOrderGrouper,
    help=__doc__,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
)


# ----------------------------------------------------------------------
@app.command("Display", no_args_is_help=False)
def Display(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Write verbose information to the terminal."),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Write debug information to the terminal."),
    ] = False,
) -> None:
    """Displays supported emojis."""

    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        emojis = _CreateEmojiTables()

        with dm.YieldStdout() as stdout_stream:
            console = Console(
                file=stdout_stream.stream,  # type: ignore
            )

            for category_name, items in emojis.items():
                if not items:
                    continue

                display_aliases = category_name != "Intentionally Skipped"

                console.rule(
                    "[bold white]{}[/]".format(category_name),
                    align="left",
                )

                table = Table(
                    show_footer=True,
                )

                for col_name, justify, footer in [
                    ("Emoji", "center", None),
                    (
                        "Emoji Name",
                        "center",
                        Text(
                            'add ":<name>:" to the commit message (e.g. ":tada:")',
                            style="italic",
                        ),
                    ),
                    ("Description", "left", None),
                    (
                        "Aliases",
                        "left",
                        Text(
                            'add ":<alias>:" to the commit message (e.g. ":+feature:")',
                            style="italic",
                        ),
                    ),
                ]:
                    if not display_aliases and col_name == "Aliases":
                        continue

                    table.add_column(
                        col_name,
                        footer or "",
                        justify=justify,  # type: ignore
                    )

                for item in items:
                    args = [item.code, item.name, item.description]

                    if display_aliases:
                        args.append(", ".join(item.aliases))

                    table.add_row(*args)

                console.print(Group("", table, ""))

            console.rule(
                "This functionality uses emojis defined by [link=https://gitmoji.dev/]gitmoji[/]"
            )


# ----------------------------------------------------------------------
@app.command("Transform", no_args_is_help=True)
def Transform(
    message_or_filename: Annotated[
        str, typer.Argument(help="Message to transform (or filename that contains the message).")
    ],
) -> None:
    """Transforms a message that contains emoji text placeholders."""

    potential_path = Path(message_or_filename)
    if potential_path.is_file():
        with potential_path.open(encoding="UTF-8") as f:
            message = f.read()
    else:
        message = message_or_filename

    emojis = _CreateEmojiTables()

    emoji_regex = re.compile(
        textwrap.dedent(
            r"""(?#
            Whole match [start]             )(?P<whole_match>:(?#
            Value                           )(?P<value>[^:]+)(?#
            Whole match [end]               ):)(?#
            )""",
        ),
    )

    # Populate aliases
    aliases: dict[str, str] = {}

    for items in emojis.values():
        for item in items:
            for alias in item.aliases:
                assert alias not in aliases, alias
                aliases[alias] = item.code

    # ----------------------------------------------------------------------
    def SubstituteAlias(
        match: Match,
    ) -> str:
        alias = match.group("value")

        emoji = aliases.get(alias, None)
        if emoji is None:
            return match.group("whole_match")

        return "{} [{}]".format(emoji, alias)

    # ----------------------------------------------------------------------

    message = emoji_regex.sub(SubstituteAlias, message)

    # Populate emojis
    emoji_codes: dict[str, str] = {}

    for items in emojis.values():
        for item in items:
            assert item.code not in emojis, item.code
            emoji_codes[item.code] = item.emoji

    # ----------------------------------------------------------------------
    def SubstituteEmojis(
        match: Match,
    ) -> str:
        whole_match = match.group("whole_match")

        emoji = emoji_codes.get(whole_match)
        if emoji is None:
            return whole_match

        return emoji

    # ----------------------------------------------------------------------

    message = emoji_regex.sub(SubstituteEmojis, message)

    sys.stdout.write(message)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class _EmojiInfo:
    name: str
    emoji: str
    code: str
    description: str
    aliases: list[str]


# ----------------------------------------------------------------------
def _CreateEmojiTables() -> dict[
    Optional[str],  # Category, None implies un-categorized
    list[_EmojiInfo],
]:
    this_path = Path(__file__).parent

    # Read the emoji data
    data_filename = this_path / "Gitmoji" / "gitmojis.json"
    assert data_filename.is_file(), data_filename

    with data_filename.open(
        "r",
        encoding="UTF-8",
    ) as f:
        data_content = json.load(f)

    assert "gitmojis" in data_content, data_content.keys()
    data_content = data_content["gitmojis"]

    # ----------------------------------------------------------------------
    @dataclass(frozen=True)
    class RawEmojiInfo(object):
        name: str
        emoji: str
        description: str

    # ----------------------------------------------------------------------

    emojis: dict[str, RawEmojiInfo] = {
        data["code"]: RawEmojiInfo(
            data["code"].replace(":", ""),
            data["emoji"],
            data["description"],
        )
        for data in data_content
    }

    # Read the category data
    categories_filename = this_path / "categories.json"
    assert categories_filename.is_file(), categories_filename

    with categories_filename.open(
        "r",
        encoding="UTF-8",
    ) as f:
        category_content = json.load(f)

    # Produce the results
    results: dict[Optional[str], list[_EmojiInfo]] = {}

    for category_item in category_content:
        category_name = category_item["category"]

        these_emojis: list[_EmojiInfo] = []

        for item in category_item["items"]:
            code = item["code"]

            raw_info = emojis.get(code, None)
            assert raw_info is not None, (category_name, code)

            these_emojis.append(
                _EmojiInfo(
                    raw_info.name,
                    raw_info.emoji,
                    code,
                    raw_info.description,
                    item["aliases"],
                ),
            )

            del emojis[code]

        assert these_emojis
        results[category_name] = these_emojis

    # Collect all the items that didn't have an explicit category
    results[None] = [
        _EmojiInfo(
            raw_info.name,
            raw_info.emoji,
            code,
            raw_info.description,
            [],
        )
        for code, raw_info in emojis.items()
    ]

    return results


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
