import re
from crew import task


@task.arg("name", type=str, desc="The package to install")
@task.arg("version", type=str, desc="The version to install")
@task.returns("The version of the installed package")
class AptgetInstall(task.BaseTask):
    """Install a package using apt-get"""

    async def verify(self) -> str:
        policy_output = await self.sh(f"apt-cache policy {self.params.esc_name}")
        m = re.search("Installed: (.*?)\n", policy_output)
        print(policy_output)
        assert m, "no version found"
        installed_version = m.group(1)
        assert installed_version != "(none)", "Installed version is (none)"
        if self.params.version:
            assert installed_version == self.params.version
        else:
            saved_version = self.state_variable(self.params.name)
            requested_version = saved_version.get()
            if requested_version:
                assert requested_version == installed_version
            else:
                saved_version.set(installed_version)
        return installed_version

    async def run(self):
        saved_version = self.state_variable(self.params.name)
        version = None
        if self.params.version:
            version = self.params.version
        elif saved_version.get():
            version = saved_version.get()
        specifier = (
            f"{self.params.esc_name}={self.esc(version)}"
            if version
            else self.params.esc_name
        )
        return await self.sh(f"apt-get install -y {specifier}")

    async def available(self) -> bool:
        code, _, _ = await self.sh_with_code("which apt-get")
        return code == 0
