from crew import task


@task.arg("path", desc="The path to check")
@task.returns("Indicates if target path is a directory")
class FsIsFile(task.BaseTask):
    """Checks if the path is a directory"""

    async def run(self) -> bool:
        code, _, _ = await self.sh_with_code(f"test -f {self.params.esc_path}")
        return code == 0
