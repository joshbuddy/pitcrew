import base64
import hashlib
from crew import task


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
            f"echo {self.esc(base64.b64encode(self.params.content).decode())} | base64 --decode | tee {self.params.esc_path} > /dev/null"
        )
