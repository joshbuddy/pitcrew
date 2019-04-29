import re
from pitcrew import task


@task.arg("name", type=str, desc="The package to install")
@task.returns("The version of the installed package")
class AptgetInstall(task.BaseTask):
    """Install a package using apt-get"""

    async def verify(self) -> str:
        policy_output = await self.sh(f"apt-cache policy {self.params.esc_name}")
        m = re.search("Installed: (.*?)\n", policy_output)
        assert m, "no version found"
        installed_version = m.group(1)
        assert installed_version != "(none)", "Installed version is (none)"
        return installed_version

    async def run(self):
        return await self.sh(f"apt-get install -y {self.params.esc_name}")

    async def available(self) -> bool:
        code, _, _ = await self.sh_with_code("which apt-get")
        return code == 0
