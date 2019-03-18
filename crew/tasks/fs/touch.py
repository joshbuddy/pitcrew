from crew import task


@task.arg("path", desc="The path to change the mode of", type=str)
class FsTouch(task.BaseTask):
    """Touches a file"""

    async def run(self):
        return await self.sh(f"touch {self.params.esc_path}")
