# CLI

## `crew sh [shell-command]`

This allows an ad-hoc command to be run across a set of contexts.

### Arguments

`-p` The provider task to use
`-P` The arguments to pass to the provider encoded as json

### Examples

List your root folder locally

`bin/crew sh ls /`

Get the time on 100 machines

`bin/crew sh -p providers.ssh -P '{"user": "root", "hosts": ["192.168.0.1-100"]}' date`

## `crew run [task-name] <task-args>`

This runs a command across a set of contexts.

### Arguments

`-p` The provider task to use
`-P` The arguments to pass to the provider encoded as json

### Examples

Create a file at `./foo` with the contents "bar".

`bin/crew run fs.write foo bar`

Install an apt package over ssh

`bin/crew run -p providers.ssh -P '{"user": "root", "hosts": ["192.168.0.1"]}' apt_get.install python3.6`

## `crew list`

This will list all tasks currently available.

## `crew info [task-name]`

Displays information about a single task

## `crew new [task-name]`

This will create a new task file.

## `crew test <prefix>`

Run tests for crew tasks. If you specify a prefix, it will only run tests which belong to tasks
matching the prefix

### Examples

This will run all task tests.

`bin/crew test`

To only run tests for tasks starting with `fs.` run:

`bin/crew test fs.`

## `crew docs`

Generates documentation for the currently available tasks in the file `docs/tasks.md`.

## `crew help`

Get help for crew commands
