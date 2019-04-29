"""Contexts allow execution of tasks. There are currently three types of
contexts: local, ssh and docker.

Local contexts run commands on the host computer running crew.

SSH contexts run commands over SSH on the target computer.

Docker contexts run commands on a running docker container.
"""

import os
import shlex
import asyncio
import asyncssh
import getpass
from typing import Tuple
from pitcrew.file import LocalFile, DockerFile, SSHFile
from pitcrew.logger import logger
from abc import ABC, abstractmethod


class ChangeUser:
    """Context manager to allow changing the user within a context"""

    def __init__(self, context, new_user):
        self.context = context
        self.old_user = context.user
        self.new_user = new_user

    def __enter__(self):
        self.context.user = self.new_user
        return self.context

    def __exit__(self, exc, value, tb):
        self.context.user = self.old_user


class ChangeDirectory:
    """Context manager to allow changing the current directory within a context"""

    def __init__(self, context, new_directory):
        self.context = context
        self.old_directory = context.directory
        if not self.old_directory:
            self.old_directory = "."
        if new_directory.startswith("/"):
            self.new_directory = new_directory
        else:
            self.new_directory = os.path.join(self.old_directory, new_directory)

    def __enter__(self):
        self.context.directory = self.new_directory
        return self.context

    def __exit__(self, exc, value, tb):
        self.context.directory = self.old_directory


class Context(ABC):
    """Abstract base class for all contexts."""

    def __init__(self, app, loader, user=None, parent_context=None, directory=None):
        self.app = app
        self.loader = loader
        self.user = user or getpass.getuser()
        self.directory = directory
        self.actual_user = None
        self.parent_context = parent_context
        self.cache = {}

    @abstractmethod
    async def sh_with_code(command, stdin=None, env=None) -> Tuple[int, bytes, bytes]:
        pass

    @abstractmethod
    async def raw_sh_with_code(command) -> Tuple[int, bytes, bytes]:
        pass

    @abstractmethod
    def descriptor(self) -> str:
        pass

    async def run_all(self, *tasks):
        for f in asyncio.as_completed(tasks):
            await f

    async def sh_ok(self, command, stdin=None, env=None) -> bool:
        code, _, _ = await self.sh_with_code(command, stdin=stdin, env=env)
        return code == 0

    async def sh(self, command, stdin=None, env=None) -> str:
        """Runs a shell command within the given context. Raises an AssertionError if it exits with
        a non-zero exitcode. Returns STDOUT encoded with utf-8."""

        logger.shell_start(self, command)
        code, out, err = await self.sh_with_code(command, stdin=stdin, env=env)
        logger.shell_stop(self, code, out, err)
        assert (
            code == 0
        ), f"expected exit code of 0, got {code} when running\n:COMMAND: {command}\nOUT: {out.decode()}\n\nERR {err.decode()}"
        return out.decode()

    def docker_context(self, *args, **kwargs) -> "DockerContext":
        """Creates a new docker context with the given container id."""
        return DockerContext(
            self.app, self.loader, *args, **kwargs, parent_context=self
        )

    def ssh_context(self, *args, **kwargs) -> "SSHContext":
        """Creates a new ssh context with the given container id."""
        return SSHContext(self.app, self.loader, *args, **kwargs, parent_context=self)

    async def fill_actual_user(self):
        if self.actual_user:
            return
        code, out, err = await self.raw_sh_with_code("whoami")
        assert code == 0, "unable to run whoami to determine the user"
        self.actual_user = out.decode().strip()
        if self.actual_user != self.user:
            print("Escalating user!")

    def with_user(self, user):
        """Returns a context handler for defining the user"""
        return ChangeUser(self, user)

    def cd(self, directory):
        """Returns a context handler for changing the directory"""
        return ChangeDirectory(self, directory)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type:
            raise exc_value.with_traceback(traceback)

    async def invoke(self, fn, *args, **kwargs):
        """Allows invoking of an async function within this context."""
        task = self.create_task(fn)
        return await task.run(*args, **kwargs)

    def create_task(self, fn):
        from pitcrew.task import BaseTask

        task_cls = type(fn.__name__, (BaseTask,), dict(run=fn))
        task = task_cls()
        task.context = self
        return task

    def has_package(self, name):
        return self.loader.has_package(name)

    def package(self, name):
        return self.loader.package(name, self)

    @property
    def local_context(self) -> "LocalContext":
        return self.app.local_context

    def file(self, path):
        return self.file_class(self, path)

    def esc(self, text):
        return shlex.quote(text)

    def __getattr__(self, name):
        if self.has_package(name):
            return self.package(name)
        else:
            return self.__getattribute__(name)

    async def _prepare_command(self, command):
        await self.fill_actual_user()
        if self.directory:
            command = f"cd {self.esc(self.directory)} && {command}"
        if self.actual_user != self.user:
            command = f"sudo -u {self.esc(self.user)} -- /bin/sh -c {self.esc(command)}"
        return command


class LocalContext(Context):
    _singleton = None
    file_class = LocalFile

    def __new__(cls, *args, **kwargs):
        if not cls._singleton:
            cls._singleton = object.__new__(LocalContext)
        return cls._singleton

    async def sh_with_code(self, command, stdin=None, env=None):
        command = await self._prepare_command(command)
        new_env = os.environ.copy()
        new_env.pop("__PYVENV_LAUNCHER__", None)
        if env:
            new_env.update(env)

        kwargs = {
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "stdin": asyncio.subprocess.PIPE,
            "env": new_env,
        }
        proc = await asyncio.create_subprocess_shell(command, **kwargs)
        stdout, stderr = await proc.communicate(input=stdin)
        return (proc.returncode, stdout, stderr)

    async def raw_sh_with_code(self, command):
        kwargs = {"stdout": asyncio.subprocess.PIPE, "stderr": asyncio.subprocess.PIPE}
        proc = await asyncio.create_subprocess_shell(command, **kwargs)
        stdout, stderr = await proc.communicate()
        return (proc.returncode, stdout, stderr)

    def descriptor(self):
        return f"{self.user}@local"


class SSHContext(Context):
    file_class = SSHFile

    def __init__(
        self,
        app,
        loader,
        host,
        port=22,
        user=None,
        parent_context=None,
        **connection_kwargs,
    ):
        self.host = host
        self.port = port
        self.async_helper = None
        self.connection = None
        self.connect_timeout = 1
        self.connection_kwargs = connection_kwargs
        super().__init__(app, loader, user=user, parent_context=parent_context)

    async def sh_with_code(self, command, stdin=None, env=None):
        command = await self._prepare_command(command)
        proc = await self.connection.run(
            command, stdin=stdin, env=env or {}, encoding=None
        )
        return (proc.exit_status, proc.stdout, proc.stderr)

    async def raw_sh_with_code(self, command):
        proc = await self.connection.run(command, encoding=None)
        return (proc.exit_status, proc.stdout, proc.stderr)

    async def __aenter__(self):
        gen = asyncio.wait_for(
            asyncssh.connect(
                self.host, port=self.port, username=self.user, **self.connection_kwargs
            ),
            timeout=self.connect_timeout,
        )
        self.connection = await gen
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.connection.close()
        await super().__aexit__(exc_type, exc_value, traceback)

    def descriptor(self):
        return f"ssh:{self.user}@{self.host}"


class DockerContext(Context):
    file_class = DockerFile

    def __init__(self, app, loader, container_id, **kwargs):
        self.container_id = container_id
        super().__init__(app, loader, **kwargs)

    async def sh_with_code(self, command, stdin=None, env=None):
        command = await self._prepare_command(command)
        env_string = ""
        if env:
            for k, v in env.items():
                env_string += f"-e {self.esc(k)}={self.esc(v)} "

        cmd = f"docker exec -i {env_string}{self.container_id} /bin/sh -c {self.esc(command)}"
        return await self.local_context.sh_with_code(cmd, stdin=stdin)

    async def raw_sh_with_code(self, command):
        return await self.local_context.raw_sh_with_code(
            f"docker exec -i {self.container_id} /bin/sh -c {self.esc(command)}"
        )

    def descriptor(self):
        return f"docker:{self.user}@{self.container_id[0:6]}"

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.local_context.docker.stop(self.container_id, time=0)
        await super().__aexit__(exc_type, exc_value, traceback)
