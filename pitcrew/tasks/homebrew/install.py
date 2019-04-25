from pitcrew import task


@task.arg("name", type=str, desc="Package to install")
@task.returns("the version installed")
class HomebrewInstall(task.BaseTask):
    """Read value of path into bytes"""

    async def verify(self) -> str:
        code, out, err = await self.sh_with_code(
            f"brew ls --versions {self.params.esc_name}"
        )
        lines = out.decode().strip().split("\n")
        if lines != [""]:
            for line in lines:
                _, version = line.split(" ", 1)
                return version
        assert False, f"no version found for {self.params.name}"

    async def run(self):
        await self.sh(f"brew install {self.params.esc_name}")

    async def available(self) -> bool:
        code, _, _ = await self.sh_with_code("which brew")
        return code == 0
