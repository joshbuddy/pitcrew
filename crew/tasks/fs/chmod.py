from crew import task


@task.arg("path", desc="The path to change the mode of", type=str)
@task.arg("mode", desc="The mode", type=str)
@task.returns("The bytes of the file")
class FsChmod(task.BaseTask):
    """Changes the file mode of the specified path"""

    async def run(self):
        return await self.sh(f"chmod {self.params.esc_mode} {self.params.esc_path}")


class FsChmodTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        with self.cd("/tmp"):
            await self.fs.touch("some-file")
            await self.fs.chmod("some-file", "644")
            assert (await self.fs.stat("some-file")).mode == "100644"
            await self.fs.chmod("some-file", "o+x")
            assert (await self.fs.stat("some-file")).mode == "100645"
