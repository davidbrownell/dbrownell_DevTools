# ----------------------------------------------------------------------
# |
# |  BuildActivities_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-02-14 10:23:43
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""Unit tests for BuildActivities.py"""

import re
import textwrap

from typing import cast

from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent
from dbrownell_DevTools.BuildActivities import *


# ----------------------------------------------------------------------
def test_UpdateVersion(tmp_path):
    repo_root = Path(__file__).parent.parent
    version_filename = tmp_path / "version.txt"

    with version_filename.open("w") as f:
        f.write(
            textwrap.dedent(
                """\
                Before
                __version__ = 0.0.0
                After
                """,
            ),
        )

    dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

    dm = cast(DoneManager, next(dm_and_content))

    UpdateVersion(
        dm,
        repo_root,
        version_filename,
        lambda content, semver: re.sub("__version__ = 0.0.0", f"__version__ = {semver}", content),
    )

    with version_filename.open() as f:
        version_content = f.read()

    match = re.match(
        r"""(?#
        )Before\n(?#
        )__version__ = (?#
        )(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)\n(?#
        )After\n(?#
        )""",
        version_content,
        flags=re.MULTILINE,
    )
    assert match
    assert match.group("major") != "0" or match.group("minor") != "0" or match.group("patch") != "0"

    content = cast(str, next(dm_and_content))
