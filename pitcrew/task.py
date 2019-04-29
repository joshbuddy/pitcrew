"""
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
"""

import os
import shlex
import inspect
import asyncio
from pitcrew.logger import logger
from pitcrew.template import Template
from pitcrew.test.util import ubuntu_decorator
from abc import ABC, abstractmethod


class Parameters:
    def __init__(self):
        self.__dict = {}

    def _set_attr(self, name, val):
        setattr(self, name, val)
        self.__dict[name] = val

    def __dict__(self):
        return self.__dict


class TaskFailureError(Exception):
    pass


class BaseTask(ABC):
    tests = []
    context = None
    use_coersion = False
    name = None
    return_value = None
    return_desc = None
    memoize = False
    nodoc = False

    @classmethod
    def expected_return_type(cls):
        if hasattr(cls, "verify"):
            sig = inspect.signature(cls.verify)
        else:
            sig = inspect.signature(cls.run)
        return sig.return_annotation

    @classmethod
    def has_return_type(cls):
        return cls.expected_return_type() != inspect.Signature.empty

    @classmethod
    def arg_struct(cls):
        s = Parameters()
        for arg in cls._args():
            s._set_attr(arg.name, arg.default)
            if arg.type == str:
                setattr(s, f"esc_{arg.name}", None)
        return s

    @classmethod
    def _args(cls):
        if not hasattr(cls, "args"):
            cls.args = []
        return cls.args

    @classmethod
    def esc(cls, text):
        return shlex.quote(text)

    @classmethod
    def name(cls):
        return cls.__name__

    @classmethod
    def desc(cls):
        return cls.__doc__

    @classmethod
    def source(cls):
        with open(inspect.getfile(cls)) as fh:
            return fh.read()

    def __getattr__(self, name):
        return getattr(self.context, name)

    def _process_args(self, *incoming_args, **incoming_kwargs):
        incoming_args = list(incoming_args)
        params = self.__class__.arg_struct()
        for arg in self.args:
            value = arg.default
            if arg.required and len(incoming_args) != 0:
                if arg.remaining:
                    value = []
                    while len(incoming_args) != 0:
                        value.append(
                            arg.process(incoming_args.pop(0), self.use_coersion)
                        )
                else:
                    value = arg.process(incoming_args.pop(0), self.use_coersion)
            elif arg.name in incoming_kwargs:
                value = arg.process(
                    incoming_kwargs.pop(arg.name, None), self.use_coersion
                )

            params._set_attr(arg.name, value)
            if value and arg.type == str and not arg.remaining:
                esc_value = self.esc(value)
                setattr(params, f"esc_{arg.name}", esc_value)

        if incoming_args:
            raise TypeError(f"got unexpected positional arguments {incoming_args}")

        if incoming_kwargs:
            raise TypeError(f"got unexpected keyword arguments {incoming_kwargs}")

        self.params = params

    def _enforce_return_type(self, value):
        expected_return_type = self.__class__.expected_return_type()
        if expected_return_type == inspect.Signature.empty and not value:
            self.return_value = value
        else:
            if not isinstance(value, expected_return_type):
                raise TypeError(
                    f"return value {value} does not conform to expected type {expected_return_type}"
                )
            self.return_value = value
        if self.__class__.memoize:
            self.context.cache[self.__class__] = value
        return value

    def coerce_inputs(self, use_coersion=True):
        self.use_coersion = use_coersion

    def invoke_sync(self, *args, **kwargs):
        if inspect.iscoroutinefunction(self.invoke):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.invoke(*args, **kwargs))
            loop.close()
        else:
            self.invoke(*args, **kwargs)

    def task_file(self, path):
        file_path = os.path.abspath(
            os.path.join(inspect.getfile(self.__class__), "..", path)
        )

        return self.context.local_context.file(file_path)

    @abstractmethod
    async def run(self):
        pass

    async def invoke_with_context(self, context, *args, **kwargs):
        self.context = context
        return await self.invoke(*args, **kwargs)

    async def invoke(self, *args, **kwargs):
        self._process_args(*args, **kwargs)

        if self.__class__.memoize and self.__class__ in self.context.cache:
            return self.context.cache[self.__class__]

        with logger.with_task(self):
            if hasattr(self, "verify"):
                return await self._invoke_with_verify()
            else:
                return await self._invoke_without_verify()

    async def _invoke_with_verify(self):
        try:
            return self._enforce_return_type(await self.verify())
        except AssertionError:
            await self.run()
            try:
                return self._enforce_return_type(await self.verify())
            except AssertionError:
                raise TaskFailureError("this task failed to run")

    async def _invoke_without_verify(self):
        return self._enforce_return_type(await self.run())

    def template(self, name):
        template_path = os.path.abspath(
            os.path.join(inspect.getfile(self.__class__), "..", name)
        )
        return Template(self, template_path)

    async def poll(self, fn):
        while True:
            try:
                await fn()
                break
            except AssertionError:
                await asyncio.sleep(1)


class Argument:
    def __init__(
        self,
        task_class,
        name,
        type=None,
        default=None,
        required=True,
        desc=None,
        remaining=False,
    ):
        if name == "env":
            raise ValueError("`env' is a reserved argument name")
        self.task_class = task_class
        self.name = name
        self.type = type or str
        self.default = default
        self.required = required
        self.desc = desc
        self.remaining = remaining

    def process(self, value, use_coersion=False):
        if use_coersion:
            value = self.coerce_from_string(value)

        if value is None:
            if self.required:
                raise Exception(f"value is required for {self.name}")
            return self.default
        elif self.type != any and not isinstance(value, self.type):
            raise Exception(
                "this doesn't match %s %s with value %s" % (self.name, self.type, value)
            )
        return value

    def coerce_from_string(self, value):
        if self.type == bytes:
            return value.encode()
        elif self.type == int:
            return int(value)
        else:
            return value

    def __str__(self):
        return f"arg {self.name} {self.type}"


class TaskTest:
    def __init__(self, context):
        self.context = context

    def __getattr__(self, name):
        return getattr(self.context, name)

    ubuntu = ubuntu_decorator


def arg(name, type=None, **kwargs):
    """Decorator to add a required argument to the task."""

    def decorator(cls):
        cls._args().insert(0, Argument(cls, name, type, **kwargs))
        return cls

    return decorator


def varargs(name, type=None, **kwargs):
    def decorator(cls):
        cls._args().insert(0, Argument(cls, name, type, remaining=True, **kwargs))
        return cls

    return decorator


def opt(name, type=None, **kwargs):
    """Decorator to add an optional argument to the task."""

    def decorator(cls):
        cls._args().insert(0, Argument(cls, name, type, required=False, **kwargs))
        return cls

    return decorator


def returns(desc):
    """Decorator to describe the return type."""

    def decorator(cls):
        cls.return_desc = desc
        return cls

    return decorator


def memoize():
    """Decorator to instruct task to memoize return within the context's cache."""

    def decorator(cls):
        cls.memoize = True
        return cls

    return decorator


def nodoc():
    """Decorator to instruct task to not generate documentation for test."""

    def decorator(cls):
        cls.nodoc = True
        return cls

    return decorator
