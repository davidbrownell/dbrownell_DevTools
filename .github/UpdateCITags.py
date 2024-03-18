# ----------------------------------------------------------------------
# |
# |  UpdateCITags.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-03-02 12:29:30
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Updates the CI git tags"""

import re
import textwrap

from pathlib import Path
from typing import Annotated, Optional

import git
import typer

from AutoGitSemVer import GetSemanticVersion
from dbrownell_Common.Streams.DoneManager import DoneManager, Flags as DoneManagerFlags
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
@app.command("UpdateTags", no_args_is_help=False)
def UpdateTags(
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Do not create tags, just print what would be done.")
    ] = False,
    yes: Annotated[
        bool, typer.Option("--yes", help="Automatically answer 'yes' to all prompts.")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Write verbose information to the terminal.")
    ] = False,
    debug: Annotated[
        bool, typer.Option("--debug", help="Write debug information to the terminal.")
    ] = False,
) -> None:
    """Update the CI git tags"""

    with DoneManager.CreateCommandLine(
        flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        if dry_run:
            yes = True

        if not yes:
            result = (
                input(
                    textwrap.dedent(
                        """\
                    This script will create "CI-<version>" tags based on the current commit and push
                    them to github.

                    Are you sure that you want to continue?

                    Type 'yes' to continue or anything else to exit: """,
                    ),
                )
                .strip()
                .lower()
            )

            yes = result in ["yes", "y"]

        if not yes:
            dm.result = 1
            return

        this_dir = Path(__file__).parent
        repo_root = this_dir.parent

        semantic_version: Optional[str] = None

        with dm.Nested("Calculating semantic version...") as semver_dm:
            semver_info = GetSemanticVersion(
                semver_dm,
                this_dir,
                include_branch_name_when_necessary=False,
                no_metadata=True,
            )

            semantic_version = semver_info.semantic_version_string

            if semver_dm.result != 0:
                return

        assert semantic_version is not None

        tag_match = re.match(
            r"""(?#
            Start of tag                    )^(?#
            [optional] Prefix               )(?P<prefix>.+?)(?#
            Major                           )(?P<major>\d+)\.(?#
            Minor                           )(?P<minor>\d+)\.(?#
            Patch                           )(?P<patch>\d+)(?#
            End of tag                      )$(?#
            )""",
            semantic_version,
        )

        if tag_match is None:
            dm.WriteError(f"'{semantic_version}' is not in a supported format.")
            return

        if dry_run:
            dm.WriteInfo(
                "\n'--dry-run' was specified on the command line; no tags will be created."
            )
            return

        repo = git.Repo(repo_root)
        tags = []

        with dm.Nested("Creating local tags..."):
            prefix = tag_match.group("prefix")
            major = tag_match.group("major")
            minor = tag_match.group("minor")
            patch = tag_match.group("patch")

            for tag_name in [
                f"{prefix}{major}.{minor}.{patch}",
                f"{prefix}{major}.{minor}",
                f"{prefix}{major}",
            ]:
                tags.append(
                    repo.create_tag(
                        tag_name,
                        message="🤖 Updated CI Version",
                        force=True,
                    ),
                )

        with dm.Nested("Pushing tags..."):
            for tag in tags:
                repo.remotes.origin.push(tag, force=True)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
