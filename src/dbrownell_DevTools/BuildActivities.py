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
from pathlib import Path
from typing import Callable, Generator, Optional, Protocol

import git

from AutoGitSemVer.Lib import GetSemanticVersion  # type: ignore [import-untyped]
from dbrownell_Common.ContextlibEx import ExitStack  # type: ignore [import-untyped]
from dbrownell_Common import PathEx  # type: ignore [import-untyped]
from dbrownell_Common.Streams.DoneManager import DoneManager  # type: ignore[import-untyped]
from dbrownell_Common import SubprocessEx  # type: ignore [import-untyped]
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
    name_suffix: Optional[str] = None,
    docker_license: Optional[str] = None,  # https://spdx.org/licenses/
    docker_description: Optional[str] = None,
) -> Optional[str]:
    create_base_image_func = create_base_image_func or _CreateDefaultBaseImage  # type: ignore

    # Extract the repo name
    repo_origin: Optional[str] = None
    last_commit: Optional[str] = None

    with dm.Nested(
        "Extracting repository info...",
        lambda: repo_origin or "<Error>",
    ):
        repo = git.Repo(repo_root)

        repo_origin = repo.remotes.origin.url.split(".git")[0]
        last_commit = repo.head.object.hexsha

    assert repo_origin is not None
    assert last_commit is not None

    # Create the base image
    with create_base_image_func(dm) as base_image_name:  # type: ignore
        if dm.result != 0:
            return None

        with _CreateDockerContainer(dm, repo_root, bootstrap_args, base_image_name) as container_id:
            if dm.result != 0:
                return None

            with _SaveTemporaryImage(dm, container_id) as temporary_image_id:
                if dm.result != 0:
                    return None

                with _CreateFinalImage(
                    dm,
                    name_suffix,
                    last_commit.lower(),
                    docker_license,
                    docker_description,
                    repo_origin,
                    temporary_image_id,
                ) as final_image_id:
                    if dm.result != 0:
                        return None

                    return final_image_id


# ----------------------------------------------------------------------
def SaveDockerImage(
    dm: DoneManager,
    docker_image: str,
    output_filename: Path,
    *,
    delete_image: bool = False,
) -> None:
    output_filename.parent.mkdir(parents=True, exist_ok=True)

    save_filename = output_filename.with_suffix("")

    if os.name == "nt":
        # ----------------------------------------------------------------------
        def WindowsPostprocess():
            # Zip the tarball
            StreamCommand(
                dm,
                "Compressing docker image...",
                f'PowerShell -Command "Compress-Archive -Path {save_filename} -DestinationPath {output_filename}"',
                lambda: PathEx.GetSizeDisplay(output_filename),
            )

        # ----------------------------------------------------------------------

        postprocess_func = WindowsPostprocess
    else:
        # ----------------------------------------------------------------------
        def StandardPostprocess():
            StreamCommand(
                dm,
                "Compressing docker image...",
                f'gzip --keep "{save_filename}"',
                lambda: PathEx.GetSizeDisplay(output_filename),
            )

            if dm.result != 0:
                return

            assert save_filename.is_file(), output_filename

        # ----------------------------------------------------------------------

        postprocess_func = StandardPostprocess

    if save_filename.is_file():
        with dm.Nested("Removing previous docker image..."):
            save_filename.unlink()

    StreamCommand(
        dm,
        "Saving docker image...",
        f'docker save --output "{save_filename}" {docker_image}',
        lambda: PathEx.GetSizeDisplay(save_filename),
    )

    if dm.result != 0:
        return

    with ExitStack(save_filename.unlink):
        if output_filename.is_file():
            with dm.Nested("Removing previous compressed docker image..."):
                output_filename.unlink()

        postprocess_func()

    if dm.result != 0:
        return

    if delete_image:
        StreamCommand(
            dm,
            "Deleting docker image...",
            f"docker image rm {docker_image}",
        )


# ----------------------------------------------------------------------
def PushDockerImage(
    dm: DoneManager,
    docker_image: str,
    container_registry_url: Optional[str] = None,
    container_registry_username: Optional[str] = None,
    *,
    delete_image: bool = True,
) -> None:
    docker_image_parts = docker_image.split("/")

    if len(docker_image_parts) == 1:
        # <image>
        pass  # Nothing to do here
    elif len(docker_image_parts) == 2:
        # <username>/<image>
        if container_registry_username is not None:
            raise Exception(
                f"The container registry username is embedded in the docker image name '{docker_image}'.",
            )

        container_registry_username = docker_image_parts[0]
        docker_image = docker_image_parts[1]
    elif len(docker_image_parts) == 3:
        # <container_registry_url>/<username>/<image>
        if container_registry_username is not None:
            raise Exception(
                f"The container registry username is embedded in the docker image name '{docker_image}'.",
            )
        if container_registry_url is not None:
            raise Exception(
                f"The container registry URL is embedded in the docker image name '{docker_image}'.",
            )

        container_registry_url = docker_image_parts[0]
        container_registry_username = docker_image_parts[1]
        docker_image = docker_image_parts[2]
    else:
        raise Exception(f"'{docker_image}' is not in a recognized format.")

    if container_registry_url is not None:
        container_registry_url = container_registry_url.lstrip("https://").rstrip("/")

    new_image_name = "{}{}{}".format(
        f"{container_registry_url}/" if container_registry_url else "",
        f"{container_registry_username}/" if container_registry_username else "",
        docker_image,
    )

    exit_func: Optional[Callable[[], None]] = None

    if new_image_name != docker_image:
        StreamCommand(
            dm,
            "Tagging docker image...",
            f"docker tag {docker_image} {new_image_name}",
        )

        if dm.result != 0:
            return

        if delete_image:
            exit_func = lambda: StreamCommand(
                dm,
                "Deleting docker image...",
                f"docker image rm {new_image_name}",
            )

    if exit_func is None:
        exit_func = lambda *args, **kwargs: None

    with ExitStack(exit_func):
        StreamCommand(
            dm,
            "Pushing docker image...",
            f"docker push {new_image_name}",
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
    name_suffix: Optional[str],
    commit_hash: str,
    docker_license: Optional[str],
    docker_description: Optional[str],
    repo_origin: str,
    temporary_image_id: str,
) -> Generator[str, None, None]:
    repo_name = repo_origin.split("/")[-1]

    image_name = f"{repo_name}:{commit_hash}{name_suffix}".lower()

    docker_filename = Path(f"{repo_name}.dockerfile")

    with dm.Nested("Creating final Dockerfile..."):
        description_label = (
            f'LABEL org.opencontainers.image.description="{docker_description}"'
            if docker_description
            else ""
        )
        license_label = (
            f'LABEL org.opencontainers.image.licenses="{docker_license}"' if docker_license else ""
        )

        with docker_filename.open("w") as f:
            f.write(
                textwrap.dedent(
                    f"""\
                    FROM {temporary_image_id}

                    WORKDIR /code

                    ENTRYPOINT ["/bin/bash", "--login"]

                    LABEL org.opencontainers.image.source={repo_origin}
                    {description_label}
                    {license_label}
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

        yield image_name
