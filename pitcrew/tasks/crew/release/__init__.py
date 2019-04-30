import re
import asyncio
from pitcrew import task


@task.arg("version", desc="The version to release", type=str)
class CrewRelease(task.BaseTask):
    """This creates a release for crew"""

    async def run(self):
        current_branch = (await self.sh("git rev-parse --abbrev-ref HEAD")).strip()
        assert "master" == current_branch, "not on master"
        assert re.match(r"\d+\.\d+\.\d+", self.params.version)
        await self.sh("mkdir -p pkg")
        await asyncio.gather(
            self.crew.release.darwin(self.params.version),
            self.crew.release.linux(self.params.version),
        )
        await self.sh(
            f"env/bin/githubrelease release joshbuddy/pitcrew create {self.params.version} --publish {self.esc('pkg/*')}"
        )
        await self.sh("env/bin/python setup.py upload")
