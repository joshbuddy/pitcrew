from pitcrew import task


@task.arg("version", desc="The version to release", type=str)
class CrewBuildDarwin(task.BaseTask):
    """This creates a PyInstaller build for crew on Darwin"""

    async def run(self):
        assert await self.facts.system.uname() == "darwin"
        await self.sh("make build")
        target = f"pkg/crew-{self.params.version}-Darwin"
        await self.sh(f"cp dist/crew {target}")
