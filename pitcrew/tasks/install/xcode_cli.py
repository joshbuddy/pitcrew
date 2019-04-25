from pitcrew import task


class InstallXcodeCli(task.BaseTask):
    """Ensures xcode is installed"""

    async def verify(self):
        assert await self.fs.is_directory("/Library/Developer/CommandLineTools")

    async def run(self):
        await self.sh("xcode-select --install")
        await self.poll(self.verify)
