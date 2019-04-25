from pitcrew import task


class InstallHomebrew(task.BaseTask):
    """Ensures xcode is installed"""

    async def verify(self):
        assert await self.sh("which brew")

    async def run(self):
        await self.sh(
            '/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'
        )
