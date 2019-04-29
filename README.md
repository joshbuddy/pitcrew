# 🔧 Pitcrew

AsyncIO-powered python DSL for running tasks locally, on docker, or over ssh.

[![CircleCI](https://circleci.com/gh/joshbuddy/pitcrew.svg?style=svg)](https://circleci.com/gh/joshbuddy/pitcrew)

## At a glance

Pitcrew makes it easy to run commands on one or a lot of machines.

### Get the time on 100 machines at once

`crew sh -p providers.ssh -P '{"user": "root", "hosts": ["192.168.0.1-100"]}' date`

### Install Homebrew on a Mac

`crew run install.homebrew`

### Host a website using S3, CloudFront & SSL

`crew run examples.deploy_pitcrew`

## Installation

### From binary

To install pitcrew in your home directory, run the following:

```
curl -fsSL "https://github.com/joshbuddy/pitcrew/releases/latest/download/crew-$(uname)" > crew
chmod u+x crew
./crew run crew.install --dest="$HOME/crew"
```

### From PyPi

To install from the Python Package Index, run the following:

```
pip install pitcrew
crew run crew.install --dest="$HOME/crew"
```

### From source

```
git clone https://github.com/joshbuddy/pitcrew
cd pitcrew
python3.6 -m venv env
env/bin/pip installer -r requirements.txt
```

## Concepts

A command or set of commands is called a **task**. A **context** runs tasks either locally, on docker or over ssh.
A **provider** generates contexts.

### Tasks

Tasks are either composed from other tasks or invoking a command on a shell.

An example of a *task* might be reading a file. `fs.read(path)` reads a file as bytes and returns it:

### `pitcrew/tasks/fs/read.py`

```python
import base64
from pitcrew import task


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

For detailed usage, see [docs/cli.md](docs/cli.md) for more details.

### Run a command

Pitcrew allows running a command using `bin/crew sh -- [shell command]`.

For example `crew sh ls /` will list the "/" directory locally.

You can run this across three hosts via ssh using `crew sh -p providers.ssh -P '{"hosts": ["192.168.0.1", "192.168.0.2", "192.168.0.3"]}' ls /`.

### Run a task

Pitcrew allows running a task using `crew run [task name] <task args>`. This will normally target your local machine unless you use the `-p` flag to select a different provider.

### See available tasks

To see all the available tasks run `crew list`. This will show all available tasks which are stored in `crew/tasks`.

### Make a new task

To see all the available tasks run `crew new [task_name]`. This will create a template of a new task.

### Run tests

To run an ad-hoc command use . For tasks use `crew run [task-name] <args>`.

### Get CLI help

To see the whole list of commands available from the command-line, run `crew help`.
