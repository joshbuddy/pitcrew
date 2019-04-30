"""File objects are created through their respective contexts. A file object can be copied into
another context via a file reference for the destination. For example, if operating in an SSH
context, this would copy from the local filesystem to that destination:

    self.local_context("/some/file").copy_to(self.file("/some/other"))


For convenience `owner`, `group` and `mode` arguments are available on the `copy_to` method to
allow setting those attributes post-copy.
"""

import os
import asyncssh
from pitcrew.logger import logger
from abc import ABC


class File(ABC):
    """Abstract base class for file-based operations"""

    def __init__(self, context, path):
        self.context = context
        self.path = path

    def __str__(self):
        return f"{self.context.descriptor()}:{self.path}"

    async def copy_to(self, dest, archive=False, owner=None, group=None, mode=None):
        """Copies a file from the source to the destination."""
        with logger.with_copy(self, dest):
            pair = (self.__class__, dest.__class__)
            if pair in copiers:
                await copiers[pair](self, dest, archive=archive)
                if owner:
                    await dest.context.fs.chown(dest.path, owner, group=group)
                if mode:
                    await dest.context.fs.chmod(dest.path, mode)
            else:
                raise Exception(f"cannot find a copier for {pair}")


class LocalFile(File):
    """A reference to a file on the local machine executing pitcrew"""

    def __init__(self, context, path):
        self.context = context
        self.path = os.path.expanduser(path)


class DockerFile(File):
    """A reference to a file on a Docker container"""

    pass


class SSHFile(File):
    """A reference to a file on a remote host accessible via SSH"""

    pass


async def local_to_local_copier(src, dest, archive=False):
    ctx = src.context
    command = "cp"
    if archive:
        command += " -a"
    command += f" {ctx.esc(src.path)} {ctx.esc(dest.path)}"
    await ctx.sh(command)


async def ssh_to_local_copier(src, dest, archive=False):
    ctx = src.context
    await asyncssh.scp(
        (ctx.connection, src.path), dest.path, recursive=archive, preserve=archive
    )


async def local_to_ssh_copier(src, dest, archive=False):
    ctx = dest.context
    await asyncssh.scp(
        src.path, (ctx.connection, dest.path), recursive=archive, preserve=archive
    )


async def docker_to_local_copier(src, dest, archive=False):
    ctx = dest.context
    command = "docker cp"
    if archive:
        command += " -a"
    command += (
        f" {ctx.esc(src.context.container_id)}:{ctx.esc(src.path)} {ctx.esc(dest.path)}"
    )
    await ctx.sh(command)


async def local_to_docker_copier(src, dest, archive=False):
    ctx = src.context
    command = "docker cp"
    if archive:
        command += " -a"
    command += f" {ctx.esc(src.path)} {ctx.esc(dest.context.container_id)}:{ctx.esc(dest.path)}"
    await ctx.sh(command)


copiers = {
    (LocalFile, LocalFile): local_to_local_copier,
    (SSHFile, LocalFile): ssh_to_local_copier,
    (LocalFile, SSHFile): local_to_ssh_copier,
    (DockerFile, LocalFile): docker_to_local_copier,
    (LocalFile, DockerFile): local_to_docker_copier,
}
