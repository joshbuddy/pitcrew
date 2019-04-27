import os
from pitcrew import task


@task.arg("url", desc="The url to clone", type=str)
@task.arg("destination", desc="The destination", type=str)
class GitClone(task.BaseTask):
    """Installs a package, optionally allowing the version number to specified.

This task defers exection to package-manager specific installation tasks, such as
homebrew or apt-get.
    """

    async def verify(self):
        git_config = await self.fs.read(
            os.path.join(self.params.destination, ".git", "config")
        )
        assert (
            self.params.url in git_config.decode()
        ), f"url {self.params.url} couldn't be found in the .git/config"

    async def run(self):
        command = f"git clone {self.params.esc_url} {self.params.esc_destination}"
        await self.sh(command)
