import re
import asyncio
import pitcrew
from pitcrew import task


@task.opt("dryrun", desc="Dry run mode", type=bool, default=True)
class CrewRelease(task.BaseTask):
    """This creates a release for crew"""

    async def run(self):
        if not self.params.dryrun:
            current_branch = (await self.sh("git rev-parse --abbrev-ref HEAD")).strip()
            assert "master" == current_branch, "dryrun=False must be run on master"

        await self.sh("pip install -r requirements-build.txt")
        version = pitcrew.__version__
        await self.sh("mkdir -p pkg")
        await asyncio.gather(
            self.crew.release.darwin(version), self.crew.release.linux(version)
        )
        await self.sh(
            f"env/bin/githubrelease release joshbuddy/pitcrew create {version} {self.esc('pkg/*')}"
        )
        if self.params.dryrun:
            await self.sh("env/bin/python setup.py upload_test")
        else:
            await self.sh("env/bin/python setup.py upload")
            print("Don't forget to go to github and hit publish!")
