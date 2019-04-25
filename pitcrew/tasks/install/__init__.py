from pitcrew import task


@task.arg("name", desc="The name of the package to install", type=str)
@task.returns("The version of the package installed")
class Install(task.BaseTask):
    """Installs a package, optionally allowing the version number to specified.

This task defers exection to package-manager specific installation tasks, such as
homebrew or apt-get.
    """

    async def run(self) -> str:
        installer_tasks = [self.homebrew.install, self.apt_get.install]
        for pkg in installer_tasks:
            task = pkg.task()
            if await task.available():
                return await task.invoke(name=self.params.name)
        raise Exception("cannot find a package manager to defer to")
