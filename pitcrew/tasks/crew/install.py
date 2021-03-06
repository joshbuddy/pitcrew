from pitcrew import task


@task.opt("dest", desc="The directory to install crew in", type=list, default="pitcrew")
class CrewInstall(task.BaseTask):
    """Installs crew in the path specified"""

    async def verify(self):
        with self.cd(self.params.dest):
            await self.sh("./env/bin/crew --help")

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
                await self.sh("env/bin/pip install -e .")
        elif platform == "linux":
            if await self.sh_ok("which apt-get"):
                await self.apt_get.update()
                await self.apt_get.install(
                    "apt-utils", "git", "python3.7", "python3.7-dev", "python3.7-venv"
                )
                await self.sh(
                    "apt-get install -y python3.7-distutils",
                    env={"DEBIAN_FRONTEND": "noninteractive"},
                )
            else:
                raise Exception(f"cannot install on this platform {platform}")

            await self.git.clone(
                "https://github.com/joshbuddy/pitcrew.git", self.params.dest
            )
            with self.cd(self.params.dest):
                await self.sh("python3.7 -m venv env")
                await self.sh("env/bin/pip install --upgrade pip wheel")
                await self.sh("env/bin/pip install -e .")

        else:
            raise Exception(f"cannot install on this platform {platform}")


class CrewInstallTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        with self.cd("/tmp"):
            # put this in to test the local copy you've got
            await self.local_context.file(".").copy_to(self.file("/tmp/pitcrew"))
            await self.sh("rm -rf /tmp/pitcrew/env")
            await self.fs.write(
                "/tmp/pitcrew/.git/config",
                b"""[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
    logallrefupdates = true
    ignorecase = true
    precomposeunicode = true
[remote "origin"]
    url = https://github.com/joshbuddy/pitcrew.git
    fetch = +refs/heads/*:refs/remotes/origin/*
""",
            )
            await self.crew.install()
