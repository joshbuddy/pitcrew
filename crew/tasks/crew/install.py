from crew import task


@task.opt("dest", desc="The directory to install crew in", type=str, default="crew")
class CrewInstall(task.BaseTask):
    """Installs crew in the path specified"""

    async def verify(self):
        with self.cd(self.params.dest):
            await self.sh("./bin/crew --help")

    async def run(self):
        platform = await self.facts.system.uname()
        if platform == "darwin":
            await self.install.xcode_cli()
            await self.install.homebrew()
            await self.install("git")
            await self.git.clone(
                "https://github.com/joshbuddy/pitcrew.git", self.params.dest
            )
            with self.cd(self.params.dest):
                await self.homebrew.install("python3")
                await self.sh("python3 -m venv --clear env")
                await self.sh("env/bin/pip install -r requirements.txt")
        elif platform == "linux":
            await self.apt_get.update()
            await self.apt_get.install("git")
            await self.apt_get.install("python3.6")
            await self.apt_get.install("python3-venv")
            await self.git.clone(
                "https://github.com/joshbuddy/pitcrew.git", self.params.dest
            )
            with self.cd(self.params.dest):
                await self.sh("python3.6 -m venv --clear env")
                await self.sh("env/bin/pip install -r requirements.txt")
        else:
            raise Exception(f"cannot install on this platform {platform}")


class CrewInstallTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        with self.cd("/tmp"):
            await self.crew.install()
