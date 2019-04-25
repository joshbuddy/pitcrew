from pitcrew import task


@task.arg("path", desc="The file to read", type=str)
@task.returns("The bytes of the file")
class FsRead(task.BaseTask):
    """Read value of path into bytes"""

    async def run(self) -> bytes:
        code, out, err = await self.sh_with_code(f"cat {self.params.esc_path}")
        assert code == 0, "exitcode was not zero"
        return out
