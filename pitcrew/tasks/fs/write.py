import hashlib
from pitcrew import task


@task.arg("path", type=str, desc="The path of the file to write to")
@task.arg("content", type=bytes, desc="The contents to write")
class FsWrite(task.BaseTask):
    """Write bytes to a file"""

    async def verify(self):
        stat = await self.fs.stat(self.params.path)
        assert len(self.params.content) == stat.size
        expected_digest = hashlib.sha256(self.params.content).hexdigest()
        actual_digest = await self.fs.digests.sha256(self.params.path)
        assert actual_digest == expected_digest

    async def run(self):
        await self.sh(
            f"tee {self.params.esc_path} > /dev/null", stdin=self.params.content
        )


class FsWriteTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        with self.cd("/tmp"):
            await self.fs.write("some-file", b"some content")
            out = await self.sh("cat some-file")
            assert out == "some content"
