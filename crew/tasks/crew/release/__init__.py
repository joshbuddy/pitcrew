import re
from crew import task


@task.arg("version", desc="The version to release", type=str)
@task.arg("name", desc="The name of the release", type=str)
class CrewRelease(task.BaseTask):
    async def run(self):
        current_branch = (await self.sh("git rev-parse --abbrev-ref HEAD")).strip()
        assert "master" == current_branch, "not on master"
        assert re.match(r"\d+\.\d+\.\d+", self.params.version)
        await self.sh("mkdir -p pkg")
        await self.run_all(
            self.crew.release.darwin(self.params.version),
            self.crew.release.linux(self.params.version),
        )
        await self.sh(
            f"env/bin/githubrelease release joshbuddy/pitcrew create {self.params.version} --publish --name {self.params.esc_name} {self.esc('pkg/*')}"
        )
