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

import os
import textwrap
import uuid

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Callable, Generator, Optional, Protocol

from AutoGitSemVer.Lib import GetSemanticVersion  # type: ignore [import-untyped]
from dbrownell_Common.ContextlibEx import ExitStack  # type: ignore [import-untyped]
from dbrownell_Common import PathEx  # type: ignore [import-untyped]
from dbrownell_Common.Streams.DoneManager import DoneManager  # type: ignore[import-untyped]
from dbrownell_Common import SubprocessEx  # type: ignore [import-untyped]
from semantic_version import Version as SemVer  # type: ignore [import-untyped]
import git


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


# ----------------------------------------------------------------------
class CreateBaseImageFunc(Protocol):
    """Callback passed to CreateDockerImage."""

    def __call__(
        self,
        dm: DoneManager,
    ) -> Generator[str, None, None]:
        """\
        Creates a base image to use as the foundation for the docker image.

        Returns (image_name, True if the docker image should be deleted)
        """
        ...  # pragma: no cover


def CreateDockerImage(
    dm: DoneManager,
    repo_root: Path,
    create_base_image_func: Optional[CreateBaseImageFunc] = None,
    bootstrap_args: str = "--package",
    name_suffix: Optional[str] = None,  # Decorates the docker image name and output file
) -> None:
    create_base_image_func = create_base_image_func or _CreateDefaultBaseImage  # type: ignore
    name_suffix = name_suffix or ""

    # Extract the repo name
    repo_name: Optional[str] = None

    with dm.Nested(
        "Extracting repository info...",
        lambda: repo_name or "<Error>",
    ):
        repo = git.Repo(repo_root)

        repo_name = repo.remotes.origin.url.split(".git")[0].split("/")[-1]

    # Create the base image
    with create_base_image_func(dm) as base_image_name:  # type: ignore
        if dm.result != 0:
            return

        with _CreateDockerContainer(dm, repo_root, bootstrap_args, base_image_name) as container_id:
            if dm.result != 0:
                return

            with _SaveTemporaryImage(dm, container_id) as temporary_image_id:
                if dm.result != 0:
                    return

                with _CreateFinalImage(
                    dm,
                    name_suffix,
                    repo_name,
                    temporary_image_id,
                ) as final_image_id:
                    if dm.result != 0:
                        return

                    _ExtractImage(
                        dm,
                        repo_root,
                        name_suffix,
                        final_image_id,
                    )


# ----------------------------------------------------------------------
def StreamCommand(
    dm: DoneManager,
    header: str,
    command_line: str,
    *suffix_funcs,
    cwd: Optional[Path] = None,
) -> None:
    with dm.Nested(
        header,
        list(suffix_funcs),
        suffix="\n",
    ) as this_dm:
        this_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

        with this_dm.YieldStream() as stream:
            this_dm.result = SubprocessEx.Stream(
                command_line,
                stream,
                cwd=cwd,
            )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@contextmanager
def _CreateDefaultBaseImage(
    dm: DoneManager,
) -> Generator[str, None, None]:
    unique_id = str(uuid.uuid4()).replace("-", "")

    docker_filename = Path(f"{unique_id}.dockerfile")

    with dm.Nested("Creating base image Dockerfile..."):
        with docker_filename.open("w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    FROM ubuntu:latest

                    RUN apt-get update \
                     && apt-get install -y \
                            build-essential \
                            curl \
                            git \
                     && apt-get clean \
                     && rm -rf /var/lib/apt/lists/*

                    SHELL ["/bin/bash", "-c"]
                    """,
                ),
            )

    with ExitStack(docker_filename.unlink):
        StreamCommand(
            dm,
            "Building base image...",
            f"docker build --tag {unique_id} --file {docker_filename.name} .",
        )

        if dm.result != 0:
            yield ""
            return

        with ExitStack(
            lambda: StreamCommand(
                dm,
                "Deleting base image...",
                f"docker image rm {unique_id}",
            ),
        ):
            yield unique_id


# ----------------------------------------------------------------------
@contextmanager
def _CreateDockerContainer(
    dm: DoneManager,
    repo_root: Path,
    bootstrap_args: str,
    base_image_name: str,
) -> Generator[str, None, None]:
    unique_id = str(uuid.uuid4()).replace("-", "")

    script_filename = repo_root / f"{unique_id}.sh"

    with dm.Nested("Creating initialization script..."):
        with script_filename.open("w", newline="\n") as f:
            f.write(
                textwrap.dedent(
                    f"""\
                    #!/bin/bash

                    git clone /local code

                    cd code
                    ./Bootstrap.sh {bootstrap_args}

                    echo "source /code/Activate.sh" >> /etc/bash.bashrc

                    . ./Activate.sh
                    pip cache purge
                    micromamba clean --all --force-pkgs-dirs --quiet --trash --yes
                    """,
                ),
            )

        script_filename.chmod(0o755)

    with ExitStack(script_filename.unlink):
        # Run docker and invoke the initialization script
        StreamCommand(
            dm,
            "Creating the temporary container...",
            f'docker run --name {unique_id} --volume "{repo_root}:/local" {base_image_name} /local/{script_filename.name}',
        )

        if dm.result != 0:
            yield ""
            return

    with ExitStack(
        lambda: StreamCommand(
            dm,
            "Deleting the temporary container...",
            f"docker container rm {unique_id}",
        ),
    ):
        yield unique_id


# ----------------------------------------------------------------------
@contextmanager
def _SaveTemporaryImage(
    dm: DoneManager,
    container_id: str,
) -> Generator[str, None, None]:
    unique_id = str(uuid.uuid4()).replace("-", "")

    StreamCommand(
        dm,
        "Saving temporary image...",
        f"docker commit {container_id} {unique_id}",
    )

    if dm.result != 0:
        yield ""
        return

    with ExitStack(
        lambda: StreamCommand(
            dm,
            "Deleting temporary image...",
            f"docker image rm {unique_id}",
        ),
    ):
        yield unique_id


# ----------------------------------------------------------------------
@contextmanager
def _CreateFinalImage(
    dm: DoneManager,
    name_suffix: str,
    repo_name: str,
    temporary_image_id: str,
) -> Generator[str, None, None]:
    now = datetime.now()
    image_name = f"{repo_name}{name_suffix}-{now.year:04d}.{now.month:02d}.{now.day:02d}-{now.hour:02d}.{now.minute:02d}.{now.second:02d}".lower()

    docker_filename = Path(f"{image_name}.dockerfile")

    with dm.Nested("Creating final Dockerfile..."):
        with docker_filename.open("w") as f:
            f.write(
                textwrap.dedent(
                    f"""\
                    FROM {temporary_image_id}

                    WORKDIR /code

                    ENTRYPOINT ["/bin/bash", "--login"]
                    """,
                ),
            )

    with ExitStack(docker_filename.unlink):
        StreamCommand(
            dm,
            "Building final image...",
            f"docker build --tag {image_name} --file {docker_filename.name} .",
        )

        if dm.result != 0:
            yield ""
            return

        with ExitStack(
            lambda: StreamCommand(
                dm,
                "Deleting final image...",
                f"docker image rm {image_name}",
            ),
        ):
            yield image_name


# ----------------------------------------------------------------------
def _ExtractImage(
    dm: DoneManager,
    repo_root: Path,
    name_suffix: str,
    final_image_id: str,
) -> None:
    if os.name == "nt":
        compressed_filename = repo_root / f"docker_image{name_suffix}.tar"

        # ----------------------------------------------------------------------
        def Postprocess():
            with ExitStack(compressed_filename.unlink):
                # Zip the tarball
                final_filename = compressed_filename.with_suffix(".tar.zip")

                if final_filename.is_file():
                    with dm.Nested("Removing previous compressed docker image..."):
                        final_filename.unlink()

                StreamCommand(
                    dm,
                    "Compressing docker image...",
                    f'PowerShell -Command "Compress-Archive -Path {compressed_filename} -DestinationPath {final_filename}"',
                    lambda: PathEx.GetSizeDisplay(final_filename),
                )

        # ----------------------------------------------------------------------

        postprocess_func = Postprocess
    else:
        compressed_filename = repo_root / f"docker_image{name_suffix}.tar.gz"
        postprocess_func = lambda *args, **kwargs: None

    if compressed_filename.is_file():
        with dm.Nested("Removing previous docker image..."):
            compressed_filename.unlink()

    StreamCommand(
        dm,
        "Saving docker image...",
        f'docker save --output "{compressed_filename}" {final_image_id}',
        lambda: PathEx.GetSizeDisplay(compressed_filename),
    )

    if dm.result != 0:
        return

    postprocess_func()
