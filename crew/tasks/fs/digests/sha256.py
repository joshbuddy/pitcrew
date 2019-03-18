import hashlib
from crew import task


@task.arg("path", desc="The path of the file to digest", type=str)
@task.returns("The sha256 digest in hexadecimal")
class FsDigestsSha256(task.BaseTask):
    """Gets sha256 digest of path"""

    async def run(self) -> str:
        platform = await self.facts.system.uname()
        if platform == "darwin":
            out = await self.sh(f"shasum -a256 {self.params.esc_path}")
            return out.split(" ")[0]
        elif platform == "linux":
            out = await self.sh(f"sha256sum {self.params.esc_path}")
            return out.split(" ")[0]
        else:
            raise Exception("not supported")


class FsDigestsSha256Test(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        content = b"Some delicious bytes"
        await self.fs.write("/tmp/some-file", content)
        expected_digest = hashlib.sha256(content).hexdigest()
        actual_digest = await self.fs.digests.sha256("/tmp/some-file")
        assert expected_digest == actual_digest, "digests are not equal"
