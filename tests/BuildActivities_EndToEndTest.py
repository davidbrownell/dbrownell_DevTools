# ----------------------------------------------------------------------
# |
# |  BuildActivities_EndToEndTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2024-02-16 07:27:38
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2024
# |  Distributed under the MIT License.
# |
# ----------------------------------------------------------------------
"""End-to-end tests for BuildActivities.py"""

import os
import re
import sys
import uuid

from pathlib import Path
from typing import Optional

from dbrownell_Common.ContextlibEx import ExitStack
from dbrownell_Common import PathEx
from dbrownell_Common import SubprocessEx
from dbrownell_Common.Streams.DoneManager import DoneManager
from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent
import pytest

from dbrownell_DevTools.BuildActivities import CreateDockerImage, StreamCommand


# ----------------------------------------------------------------------
def SkipCreateDockerImageDecorator():
    should_skip = False
    reason = ""

    result = SubprocessEx.Run("docker info")

    if result.returncode != 0:
        should_skip = True
        reason = "Docker is not running"
    elif os.name == "nt" and "OSType: windows" in result.output:
        should_skip = True
        reason = "Docker is configured to build windows containers"

    return pytest.mark.skipif(should_skip, reason=reason)


# ----------------------------------------------------------------------
@SkipCreateDockerImageDecorator()
def test_CreateDockerImage():
    unique_id = str(uuid.uuid4()).replace("-", "")
    repo_root = Path(__file__).parent.parent

    sys.stdout.write("\n")
    with DoneManager.Create(sys.stdout, "Testing") as dm:
        with dm.Nested("Creating docker image...") as creating_dm:
            image_name = CreateDockerImage(
                creating_dm,
                repo_root,
                bootstrap_args="--package --verbose",
                docker_name_suffix=unique_id,
            )

            assert creating_dm.result == 0
            assert image_name is not None

        with dm.Nested("Testing docker image...") as test_dm:
            with ExitStack(
                lambda: StreamCommand(
                    test_dm,
                    "Deleting image...",
                    f'docker image rm "{image_name}"',
                ),
            ):
                with test_dm.Nested("Running container...") as run_dm:
                    with run_dm.Nested("Starting container..."):
                        # Start the container
                        result = SubprocessEx.Run(
                            f"docker run -itd --volume {repo_root}:/local {image_name}"
                        )
                        assert result.returncode == 0, result.output

                        container_id = result.output.strip()

                    # ----------------------------------------------------------------------
                    def StopAndDelete():
                        StreamCommand(
                            run_dm,
                            "Stopping container...",
                            f"docker stop {container_id}",
                        )
                        assert run_dm.result == 0

                        StreamCommand(
                            run_dm,
                            "Deleting container...",
                            f"docker container rm {container_id}",
                        )
                        assert run_dm.result == 0

                    # ----------------------------------------------------------------------

                    with ExitStack(StopAndDelete):
                        with run_dm.Nested("Testing container..."):
                            # Note that it isn't possible to automate the execution of scripts within
                            # the container, as it is configured to activate the local environment
                            # when logging in isn't considered to be an interactive shell when running
                            # a container with a command. And, it doesn't seem possible to exec python
                            # when operating on a started container. So, instead of running the
                            # functionality, we use the presence of files to determine if the image has
                            # been built correctly.
                            #
                            # There is almost certainly a better way to do this.

                            # Check for the presence of files
                            result = SubprocessEx.Run(f"docker exec {container_id} ls -al")
                            assert result.returncode == 0, result.output
                            assert "Activate.sh" in result.output
                            assert "Deactivate.sh" in result.output

                            # Copy Build.py locally
                            copied_build_filename = f"Build.py-{container_id}"

                            result = SubprocessEx.Run(
                                f"docker exec {container_id} cp Build.py /local/{copied_build_filename}"
                            )
                            assert result.returncode == 0, result.output

                            copied_build_filename = PathEx.EnsureFile(
                                repo_root / copied_build_filename
                            )

                            with ExitStack(copied_build_filename.unlink):
                                original_build_filename = PathEx.EnsureFile(repo_root / "Build.py")

                                with copied_build_filename.open() as f:
                                    copied_build_content = f.read()

                                with original_build_filename.open() as f:
                                    original_build_content = f.read()

                                assert copied_build_content == original_build_content
