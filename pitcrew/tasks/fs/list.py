from pitcrew import task


@task.arg("path", desc="The file to read", type=str)
@task.returns("The bytes of the file")
class FsList(task.BaseTask):
    """List the files in a directory."""

    async def run(self) -> list:
        out = await self.sh(f"ls -1 {self.params.esc_path}")
        return out.strip().split("\n")
