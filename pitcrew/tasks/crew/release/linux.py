from pitcrew import task


@task.arg("version", desc="The version to release", type=str)
class CrewBuildLinux(task.BaseTask):
    async def run(self):
        container_id = await self.docker.run("ubuntu", detach=True, interactive=True)
        docker_ctx = self.docker_context(container_id, user="root")

        async with docker_ctx:
            assert (
                await docker_ctx.facts.system.uname() == "linux"
            ), "the platform is not linux!"
            await self.file(".").copy_to(docker_ctx.file("/tmp/crew"))
            await docker_ctx.apt_get.update()
            await docker_ctx.apt_get.install("python3.6")
            await docker_ctx.apt_get.install("python3.6-dev")
            await docker_ctx.apt_get.install("python3-venv")
            await docker_ctx.apt_get.install("build-essential")
            with docker_ctx.cd("/tmp/crew"):
                await docker_ctx.sh("python3.6 -m venv --clear env")
                await docker_ctx.sh("env/bin/pip install -r requirements.txt")
                await docker_ctx.sh("make build")
                target = f"pkg/crew-{self.params.version}-linux"
                await docker_ctx.file("/tmp/crew/dist/crew").copy_to(self.file(target))
