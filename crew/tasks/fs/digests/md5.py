import hashlib
from crew import task


@task.arg("path", desc="The path of the file to digest", type=str)
@task.returns("The md5 digest in hexadecimal")
class FsDigestsMd5(task.BaseTask):
    """Gets md5 digest of path"""

    async def run(self) -> str:
        platform = await self.facts.system.uname()
        if platform == "darwin":
            out = await self.sh(f"md5 {self.params.esc_path}")
            return out.strip().split(" ")[-1]
        elif platform == "linux":
            out = await self.sh(f"md5sum {self.params.esc_path}")
            return out.split(" ")[0]
        else:
            raise Exception("not supported")


class FsDigestsMd5Test(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        content = b"Some delicious bytes"
        await self.fs.write("/tmp/some-file", content)
        expected_digest = hashlib.md5(content).hexdigest()
        actual_digest = await self.fs.digests.md5("/tmp/some-file")
        assert expected_digest == actual_digest, "digests are not equal"
