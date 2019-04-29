import re
from pitcrew import task


@task.varargs("packages", type=str, desc="The package to install")
@task.returns("The version of the installed package")
class AptgetInstall(task.BaseTask):
    """Install a package using apt-get"""

    async def verify(self) -> list:
        versions = []
        for p in self.params.packages:
            versions.append(await self.get_version(p))
        return versions

    async def run(self):
        packages = " ".join(map(lambda p: self.esc(p), self.params.packages))
        return await self.sh(f"apt-get install -y {packages}")

    async def available(self) -> bool:
        code, _, _ = await self.sh_with_code("which apt-get")
        return code == 0

    async def get_version(self, name) -> str:
        policy_output = await self.sh(f"apt-cache policy {self.esc(name)}")
        m = re.search("Installed: (.*?)\n", policy_output)
        assert m, "no version found"
        installed_version = m.group(1)
        assert installed_version != "(none)", "Installed version is (none)"
        return installed_version
