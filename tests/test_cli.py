import os
from click.testing import CliRunner
import unittest
from crew.cli import cli


class TestCli(unittest.TestCase):
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["help"])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue("Commands" in result.output)
        self.assertTrue("Usage" in result.output)
        self.assertTrue("Options" in result.output)

    def test_docs(self):
        with open("docs/tasks.md") as fh:
            expected_tasks = fh.read()
        os.remove("docs/tasks.md")
        runner = CliRunner()
        result = runner.invoke(cli, ["docs"])
        self.assertEqual(result.exit_code, 0)
        with open("docs/tasks.md") as fh:
            self.assertEqual(fh.read(), expected_tasks)

    def test_info(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["info", "fs.write"])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue("fs.write\n" in result.output)

    def test_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["list"])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(len(result.output.split("\n")) > 10)

    def test_new(self):
        task_path = os.path.abspath(
            os.path.join(
                __file__, "..", "..", "crew", "tasks", "some", "kind", "of", "task.py"
            )
        )
        try:
            runner = CliRunner()
            result = runner.invoke(cli, ["new", "some.kind.of.task"])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(os.path.isfile(task_path))
        finally:
            os.remove(task_path)

    def test_run(self):
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(cli, ["run", "fs.read", "requirements.txt"])
        self.assertEqual(result.exit_code, 0)

        with open("requirements.txt", "rb") as fh:
            contents = fh.read()
            self.assertEqual(result.stdout_bytes, contents)

    def test_test(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["test", "fs.digests.md5"])
        self.assertEqual(result.exit_code, 0)
