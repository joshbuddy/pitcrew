from crew import task


@task.arg("version", desc="The version to release", type=str)
class CrewBuildDarwin(task.BaseTask):
    async def run(self):
        assert await self.facts.system.uname() == "darwin"
        await self.sh("make build")
        target = f"pkg/crew-{self.params.version}-darwin"
        await self.sh(f"cp dist/crew {target}")
