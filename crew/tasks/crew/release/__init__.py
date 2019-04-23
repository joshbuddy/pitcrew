import re
from crew import task


@task.arg("version", desc="The version to release", type=str)
class CrewRelease(task.BaseTask):
    async def run(self):
        assert "master" == await self.sh(
            "git rev-parse --abbrev-ref HEAD"
        ), "not on master"
        assert re.match(r"\d+\.\d+\.\d+", self.params.version)
        await self.sh("mkdir -p pkg")
        await self.crew.release.darwin(self.params.version)
        await self.crew.release.linux(self.params.version)
        name = "brand new release"
        await self.sh(
            f"env/bin/githubrelease release joshbuddy/pitcrew create {self.params.version} --publish --name {self.esc(name)} {self.esc('pkg/*')}"
        )
