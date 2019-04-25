from pitcrew import task


@task.arg("path", desc="The path to change the mode of", type=str)
@task.arg("owner", desc="The owner", type=str)
@task.opt("group", desc="The owner", type=str)
@task.returns("The bytes of the file")
class FsChown(task.BaseTask):
    """Changes the file mode of the specified path"""

    async def run(self):
        owner_str = self.params.owner
        if self.params.group:
            owner_str += f":{self.params.group}"
        return await self.sh(f"chown {self.esc(owner_str)} {self.params.esc_path}")
