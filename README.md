# Crew

AsyncIO-powered python DSL for doing things to systems locally, on docker, or over ssh.

Crew does this through two concepts *tasks* and *contexts*.

A *task* can perform any system operation by calling other tasks or invoking a command on a shell.

A *context* is a place where these tasks can be performed, such as over ssh, locally or
on a running docker container.

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

An example of a *context* might be over ssh, or even locally. Learn more about contexts at [docs/api.md#crewcontext](docs/api.md#crewcontext).

## Installation

(still working on this)

## Usage

### `bin/crew list`

Lists tasks.

### `bin/crew new [task-name]`

Creates a new task.

### `bin/crew info [task-name]`

Shows information for a single task.

### `bin/crew run [task-name] <args>`

Runs a task.

### `bin/crew docs`

Generates docs in the docs directory.

### `bin/crew help`

Prints out help
