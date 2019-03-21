import json
import sys
import asyncio
import click
import argparse
import base64
from typing import Tuple, Dict
from crew.app import App


@click.group(invoke_without_command=False)
@click.version_option()
@click.pass_context
def cli(ctx):
    pass


@cli.command(
    short_help="run a command",
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True,
        "allow_interspersed_args": True,
    },
)
@click.argument("task_name")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
@click.option("--provider", default="providers.local()")
@click.pass_context
def run(ctx, *, provider, task_name, extra_args):
    async def run_task():
        async with App() as app:
            task = app.load(task_name)
            task.coerce_inputs(True)
            parser = argparse.ArgumentParser(description=task.__doc__)
            for arg in task.args:
                if arg.required:
                    parser.add_argument(arg.name, help=arg.desc)
                else:
                    parser.add_argument(f"--{arg.name}", help=arg.desc)

            parsed_task_args = parser.parse_args(extra_args)
            dict_args = vars(parsed_task_args)
            sys.stderr.write(
                f"Invoking \033[1m{task_name}\033[0m \033[1m{dict_args}\033[0m with provider \033[1m{provider}\033[0m\n"
            )

            async def provider_fn(self) -> Tuple[Dict, Dict]:
                results = {}
                failures = {}
                generator = await eval(f"self.{provider}")
                async for context in generator:
                    results[context.descriptor()] = await task.invoke_with_context(
                        context, **dict_args
                    )
                return results, failures

            class OutputEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, bytes):
                        try:
                            return obj.decode("utf-8", "strict")
                        except UnicodeDecodeError:
                            return base64.b64encode(obj)
                    else:
                        return json.JSONEncoder.default(self, obj)

            results, failures = await app.local_context.invoke(provider_fn)
            if results:
                sys.stderr.write("Result:\n")
                sys.stdout.write(json.dumps(results, cls=OutputEncoder))
                sys.stdout.flush()
                sys.stderr.write("\n")
            if failures:
                sys.stderr.write("Failures:\n")
                sys.stderr.write(str(failures))
                sys.stderr.write("\n")
                sys.stderr.flush()
            sys.stderr.write(
                f"\nSummary (results={len(results)} failures={len(failures)})"
            )
            sys.stderr.write(f"\n 🔧🔧🔧 Done! 🔧🔧🔧\n")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_task())


@cli.command(short_help="list all tasks")
@click.pass_context
def list(ctx):
    app = App()
    for task in app.loader.each_task():
        if task.nodoc:
            continue
        short_desc = (
            task.__doc__.split("\n")[0]
            if task.__doc__
            else "\033[5m(no description)\033[0m"
        )
        print(f"\033[1m{task.task_name}\033[0m {short_desc}")


@cli.command(short_help="info a command")
@click.argument("task_name")
@click.pass_context
def info(ctx, *, task_name):
    task = App().load(task_name)
    print("\033[1mName\033[0m")
    print(task_name)
    print("\033[1mDescription\033[0m")
    print(task.__doc__)
    print("\033[1mArguments\033[0m")
    for arg in task.args:
        print(f"{arg.name} ({arg.type.__name__}): {arg.desc}")

    if task.has_return_type():
        print("\033[1mReturns\033[0m")
        print(f"{task.expected_return_type().__name__}: {task.return_desc}")


@cli.command(short_help="generate docs")
@click.pass_context
def docs(ctx):
    html = App().docs().generate()
    with open("docs/tasks.md", "w") as fh:
        fh.write(html)

    print(f"Docs generated at docs/tasks.md")


@cli.command(short_help="run tests")
@click.argument("task_prefix", nargs=-1)
@click.pass_context
def test(ctx, task_prefix):
    async def run_tests():
        async with App() as app:
            await app.test_runner().run(task_prefix)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_tests())
    print(f"Tests complete")


@cli.command(short_help="create a new task")
@click.argument("task_name")
@click.pass_context
def new(ctx, task_name):
    app = App()
    app.create_task(task_name)
    print(f"Task created!")


@cli.command(short_help="show help")
@click.pass_context
def help(ctx):
    click.echo(ctx.parent.get_help())


if __name__ == "__main__":
    cli()
