# pitcrew.task

Tasks are defined by putting them in the crew/tasks directory. Tasks must inherit
from `crew.task.BaseTask`. Inside a task the main ways of interacting with the
system is through running other tasks, using `self.sh` or `self.sh_with_code`.

### Running other tasks

This is accomplished by calling through `self.{task_name}`. For instance, to
run the task `fs.write` located at `crew/tasks/fs/write.py` you'd call
`self.fs.write("/tmp/path", b"some contents")`.

### Running commands

There are two ways of running commands, `self.sh` and `self.sh_with_code`.

`self.sh` accepts a command an optional environment. It returns the stdout
of the run command as a string encoded with utf-8. If the command exits
with a non-zero status an assertion exception is raised.

`self.sh_with_code` accepts a command and an optional environment. It returns
a tuple of (code, stdout, stderr) where stdout and stderr are bytes.

### Lifecycle of a task

Tasks come in two flavors, tasks with verification and tasks without verification.
All tasks must implement a `run` method.

If a task has a validate method it performs the following:

1. Run `validate()`, return response and stop if no assertion error is raised
2. Run `run()` method
3. Run `validate()` method and raise any errors it produces, or return its return value.

If a task doesn't have a validate method it performs the following:

1. Run `run()` method.

### Tests

To add tests to a task, add test classes to your test file. For example:

```python
class FsDigestsSha256Test(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        content = b"Some delicious bytes"
        await self.fs.write("/tmp/some-file", content)
        expected_digest = hashlib.sha256(content).hexdigest()
        actual_digest = await self.fs.digests.sha256("/tmp/some-file")
        assert expected_digest == actual_digest, "digests are not equal"
```

## BaseTask
```python
BaseTask(self, /, *args, **kwargs)
```

### memoize
bool(x) -> bool

Returns True when the argument x is true, False otherwise.
The builtins True and False are the only two instances of the class bool.
The class bool is a subclass of the class int, and cannot be subclassed.
### nodoc
bool(x) -> bool

Returns True when the argument x is true, False otherwise.
The builtins True and False are the only two instances of the class bool.
The class bool is a subclass of the class int, and cannot be subclassed.
### tests
Built-in mutable sequence.

If no argument is given, the constructor creates a new empty list.
The argument must be an iterable if specified.
### use_coersion
bool(x) -> bool

Returns True when the argument x is true, False otherwise.
The builtins True and False are the only two instances of the class bool.
The class bool is a subclass of the class int, and cannot be subclassed.
### invoke_sync
```python
BaseTask.invoke_sync(self, *args, **kwargs)
```
Invokes the task synchronously and returns the result.
### task_file
```python
BaseTask.task_file(self, path)
```
Gets a file relative to the task being executed.
## arg
```python
arg(name, type=None, **kwargs)
```
Decorator to add a required argument to the task.
## opt
```python
opt(name, type=None, **kwargs)
```
Decorator to add an optional argument to the task.
## returns
```python
returns(desc)
```
Decorator to describe the return type.
## memoize
```python
memoize()
```
Decorator to instruct task to memoize return within the context's cache.
## nodoc
```python
nodoc()
```
Decorator to instruct task to not generate documentation for test.
# pitcrew.context
Contexts allow execution of tasks. There are currently three types of
contexts: local, ssh and docker.

Local contexts run commands on the host computer running crew.

SSH contexts run commands over SSH on the target computer.

Docker contexts run commands on a running docker container.

## ChangeUser
```python
ChangeUser(self, context, new_user)
```
Context manager to allow changing the user within a context
## ChangeDirectory
```python
ChangeDirectory(self, context, new_directory)
```
Context manager to allow changing the current directory within a context
## Context
```python
Context(self, app, loader, user=None, parent_context=None, directory=None)
```
Abstract base class for all contexts.
### sh
```python
Context.sh(self, command, stdin=None, env=None) -> str
```
Runs a shell command within the given context. Raises an AssertionError if it exits with
a non-zero exitcode. Returns STDOUT encoded with utf-8.
### docker_context
```python
Context.docker_context(self, *args, **kwargs) -> 'DockerContext'
```
Creates a new docker context with the given container id.
### ssh_context
```python
Context.ssh_context(self, *args, **kwargs) -> 'SSHContext'
```
Creates a new ssh context with the given container id.
### with_user
```python
Context.with_user(self, user)
```
Returns a context handler for defining the user
### cd
```python
Context.cd(self, directory)
```
Returns a context handler for changing the directory
### invoke
```python
Context.invoke(self, fn, *args, **kwargs)
```
Allows invoking of an async function within this context.
## LocalContext
```python
LocalContext(self, app, loader, user=None, parent_context=None, directory=None)
```

### LocalFile
```python
LocalContext.LocalFile(self, context, path)
```
A reference to a file on the local machine executing pitcrew
## SSHContext
```python
SSHContext(self, app, loader, host, port=22, user=None, parent_context=None, **connection_kwargs)
```

### SSHFile
```python
SSHContext.SSHFile(self, context, path)
```
A reference to a file on a remote host accessible via SSH
## DockerContext
```python
DockerContext(self, app, loader, container_id, **kwargs)
```

### DockerFile
```python
DockerContext.DockerFile(self, context, path)
```
A reference to a file on a Docker container
# pitcrew.file
File objects are created through their respective contexts. A file object can be copied into
another context via a file reference for the destination. For example, if operating in an SSH
context, this would copy from the local filesystem to that destination:

    self.local_context("/some/file").copy_to(self.file("/some/other"))


For convenience `owner`, `group` and `mode` arguments are available on the `copy_to` method to
allow setting those attributes post-copy.

## File
```python
File(self, context, path)
```
Abstract base class for file-based operations
### copy_to
```python
File.copy_to(self, dest, archive=False, owner=None, group=None, mode=None)
```
Copies a file from the source to the destination.
## LocalFile
```python
LocalFile(self, context, path)
```
A reference to a file on the local machine executing pitcrew
## DockerFile
```python
DockerFile(self, context, path)
```
A reference to a file on a Docker container
## SSHFile
```python
SSHFile(self, context, path)
```
A reference to a file on a remote host accessible via SSH
