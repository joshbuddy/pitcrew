# Crew

AsyncIO-powered python DSL for running tasks locally, on docker, or over ssh.

[![CircleCI](https://circleci.com/gh/joshbuddy/crew.svg?style=svg)](https://circleci.com/gh/joshbuddy/crew)

## At a glance

Crew makes it easy to run commands on one or a lot of machines.

### Get the time on 100 machines at once

`bin/crew sh -p providers.ssh -P '{"user": "root", "hosts": ["192.168.0.1-100"]}' date`

### Install Homebrew on a Mac

`bin/crew run install.homebrew`

### Host a website using S3, CloudFront & SSL

`bin/crew run examples.deploy_pitcrew`

## Installation

(still working on this)

## Concepts

A command or set of commands is called a **task**. A **context** runs tasks either locally, on docker or over ssh.
A **provider** generates contexts.

### Tasks

Tasks are either composed from other tasks or invoking a command on a shell.

An example of a *task* might be reading a file. `fs.read(path)` reads a file as bytes and returns it:

### `crew/tasks/fs/read.py`

```python
import base64
from crew import task


@task.arg("path", desc="The file to read", type=str)
@task.returns("The bytes of the file")
class FsRead(task.BaseTask):
    """Read value of path into bytes"""

    async def run(self) -> bytes:
        code, out, err = await self.sh_with_code(f"cat {self.params.esc_path}")
        assert code == 0, "exitcode was not zero"
        return out

```

Other tasks might include writing a file, installing xcode or cloning a git repository. All the currently available
tasks are listed at [docs/tasks.md](docs/tasks.md). The api available in a task is available at [docs/api.md#crewtask](docs/api.md#crewtask).

### Contexts

An example of a *context* might be over ssh, or even locally. Learn more about contexts at [docs/api.md#crewcontext](docs/api.md#crewcontext).

### Providers

A *provider* is a task with a specific return type. The return type is an async iterator which returns contexts.

## Usage

### Run a command

Crew allows running a command using `bin/crew sh -- [shell command]`.

For example `bin/crew sh -- ls /` will list the "/" directory locally.

You can run this across three hosts via ssh using `bin/crew sh -p providers.ssh -P '{"hosts": ["192.168.0.1", "192.168.0.2", "192.168.0.3"]}' -- ls /`.

See [docs/cli.md#run](docs/cli.md#sh) for more details.

### Run a task

Crew allows running a task using `bin/crew run [task name] <task args>`. This will normally target your local machine unless you use the `-p` flag to select a different provider. See [docs/cli.md#run](docs/cli.md#run) for more details.

### See available tasks

To see all the available tasks run `bin/crew list`. This will show all available tasks which are stored in `crew/tasks`. See [docs/cli.md#run](docs/cli.md#list) for more details.

### Make a new task

To see all the available tasks run `bin/crew new [task_name]`. This will create a template of a new task. For example if

### Run tests

To run an ad-hoc command use . For tasks use `bin/crew run [task-name] <args>`

### Get CLI help

To see the whole list of commands available from the command-line, run `bin/crew help`.
