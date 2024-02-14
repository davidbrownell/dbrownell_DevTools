# ----------------------------------------------------------------------
# |
# |  BuildActivities.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-02-14 10:04:19
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Functionality often invoked as part of a build process"""

from pathlib import Path
from typing import Callable, Optional

from AutoGitSemVer.Lib import GetSemanticVersion  # type: ignore [import-untyped]
from dbrownell_Common.Streams.DoneManager import DoneManager  # type: ignore[import-untyped]
from semantic_version import Version as SemVer  # type: ignore [import-untyped]


# ----------------------------------------------------------------------
def UpdateVersion(
    dm: DoneManager,
    source_root: Path,
    version_filename: Path,
    version_replacement_func: Callable[[str, SemVer], str],
) -> None:
    semantic_version: Optional[SemVer] = None

    with dm.Nested("Calculating version...") as version_dm:
        result = GetSemanticVersion(
            version_dm,
            source_root,
            include_branch_name_when_necessary=False,
            no_metadata=True,
        )

        semantic_version = result.semantic_version

    with dm.Nested("Updating '{}'...".format(version_filename)):
        with version_filename.open("r") as f:
            content = f.read()

        content = version_replacement_func(content, semantic_version)

        with version_filename.open("w") as f:
            f.write(content)
