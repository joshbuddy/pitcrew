from crew import task


@task.arg("image", desc="The image to run", type=str)
@task.opt(
    "detach",
    desc="Run container in background and print container ID",
    default=False,
    type=bool,
)
@task.opt("tty", desc="Allocate a pseudo-TTY", default=False, type=bool)
@task.opt("interactive", desc="Interactive mode", default=False, type=bool)
@task.opt("publish", desc="Publish ports", type=list)
@task.returns("The container id")
class DockerRun(task.BaseTask):
    """Runs a specific docker image"""

    async def run(self) -> str:
        flags = []
        if self.params.detach:
            flags.append("d")
        if self.params.tty:
            flags.append("t")
        if self.params.interactive:
            flags.append("i")

        flag_string = f" -{''.join(flags)}" if flags else ""

        if self.params.publish:
            flag_string += f" -p {' '.join(self.params.publish)}"

        out = await self.sh(f"docker run{flag_string} {self.params.esc_image}")
        return out.strip()
