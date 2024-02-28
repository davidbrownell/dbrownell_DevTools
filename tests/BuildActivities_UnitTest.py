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
from unittest.mock import MagicMock as Mock, patch

import pytest

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


# ----------------------------------------------------------------------
def test_SaveDockerImage():
    with (
        patch("dbrownell_DevTools.BuildActivities.SubprocessEx.Stream", return_value=0) as mock,
        patch("dbrownell_Common.PathEx.GetSizeDisplay", side_effect=["1KB", "2KB"]),
        patch.object(Path, "is_file", return_value=True),
        patch.object(Path, "unlink", return_value=True),
    ):
        dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

        SaveDockerImage(
            cast(DoneManager, next(dm_and_content)),
            "the_docker_image_name",
            Path("my_saved_image.tar.compressed"),
        )

        # Validate the commands
        commands = [call.args[0] for call in mock.call_args_list]

        assert len(commands) == 2
        assert commands[0] == 'docker save --output "my_saved_image.tar" the_docker_image_name'

        if os.name == "nt":
            assert (
                commands[1]
                == 'PowerShell -Command "Compress-Archive -Path my_saved_image.tar -DestinationPath my_saved_image.tar.compressed"'
            )
        else:
            assert commands[1] == 'gzip --keep "my_saved_image.tar"'

        # Validate the output
        content = cast(str, next(dm_and_content))

        assert content == textwrap.dedent(
            """\
            Heading...
              Removing previous docker image...DONE! (0, <scrubbed duration>)
              Saving docker image...DONE! (0, <scrubbed duration>, 1KB)

              Removing previous compressed docker image...DONE! (0, <scrubbed duration>)
              Compressing docker image...DONE! (0, <scrubbed duration>, 2KB)

            DONE! (0, <scrubbed duration>)
            """,
        )


# ----------------------------------------------------------------------
class TestPushDockerImage:
    # ----------------------------------------------------------------------
    def test_UsernameError1(self):
        with pytest.raises(
            Exception,
            match=re.escape(
                "The container registry username is embedded in the docker image name 'username/foo'."
            ),
        ):
            PushDockerImage(Mock(), "username/foo", container_registry_username="a_user")

    # ----------------------------------------------------------------------
    def test_UsernameError2(self):
        with pytest.raises(
            Exception,
            match=re.escape(
                "The container registry username is embedded in the docker image name 'ghcr.io/username/foo'."
            ),
        ):
            PushDockerImage(Mock(), "ghcr.io/username/foo", container_registry_username="a_user")

    # ----------------------------------------------------------------------
    def test_RegistryError(self):
        with pytest.raises(
            Exception,
            match=re.escape(
                "The container registry URL is embedded in the docker image name 'ghcr.io/username/foo'."
            ),
        ):
            PushDockerImage(Mock(), "ghcr.io/username/foo", container_registry_url="dockerhub.com")

    # ----------------------------------------------------------------------
    def test_ErrorInvalidFormat(self):
        with pytest.raises(
            Exception,
            match=re.escape("'one/two/three/four' is not in a recognized format."),
        ):
            PushDockerImage(Mock(), "one/two/three/four")

    # ----------------------------------------------------------------------
    def test_SameName(self):
        commands, output = self._Execute("the_image")

        assert commands == [
            "docker push the_image",
        ]

        assert output == textwrap.dedent(
            """\
            Heading...
              Pushing docker image...DONE! (0, <scrubbed duration>)

            DONE! (0, <scrubbed duration>)
            """,
        )

    # ----------------------------------------------------------------------
    def test_WithUsername(self):
        commands, output = self._Execute("the_image", container_registry_username="a_user")

        assert commands == [
            "docker tag the_image a_user/the_image",
            "docker push a_user/the_image",
            "docker image rm a_user/the_image",
        ]

        assert output == textwrap.dedent(
            """\
            Heading...
              Tagging docker image...DONE! (0, <scrubbed duration>)

              Pushing docker image...DONE! (0, <scrubbed duration>)

              Deleting docker image...DONE! (0, <scrubbed duration>)

            DONE! (0, <scrubbed duration>)
            """,
        )

    # ----------------------------------------------------------------------
    def test_WithUsernameNoDelete(self):
        commands, output = self._Execute(
            "the_image",
            container_registry_username="a_user",
            delete_image=False,
        )

        assert commands == [
            "docker tag the_image a_user/the_image",
            "docker push a_user/the_image",
        ]

        assert output == textwrap.dedent(
            """\
            Heading...
              Tagging docker image...DONE! (0, <scrubbed duration>)

              Pushing docker image...DONE! (0, <scrubbed duration>)

            DONE! (0, <scrubbed duration>)
            """,
        )

    # ----------------------------------------------------------------------
    def test_WithRegistryAndUsername(self):
        commands, output = self._Execute(
            "the_image",
            container_registry_url="ghcr.io",
            container_registry_username="a_user",
        )

        assert commands == [
            "docker tag the_image ghcr.io/a_user/the_image",
            "docker push ghcr.io/a_user/the_image",
            "docker image rm ghcr.io/a_user/the_image",
        ]

        assert output == textwrap.dedent(
            """\
            Heading...
              Tagging docker image...DONE! (0, <scrubbed duration>)

              Pushing docker image...DONE! (0, <scrubbed duration>)

              Deleting docker image...DONE! (0, <scrubbed duration>)

            DONE! (0, <scrubbed duration>)
            """,
        )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _Execute(*args, **kwargs) -> tuple[list[str], str]:
        with patch(
            "dbrownell_DevTools.BuildActivities.SubprocessEx.Stream", return_value=0
        ) as mock:
            dm_and_content = GenerateDoneManagerAndContent(expected_result=0)

            PushDockerImage(cast(DoneManager, next(dm_and_content)), *args, **kwargs)

            return [call.args[0] for call in mock.call_args_list], cast(str, next(dm_and_content))
