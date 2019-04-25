from pitcrew import task


@task.arg("container_id", desc="The container id to stop", type=str)
@task.opt(
    "time", desc="Seconds to wait for stop before killing it", type=int, default=10
)
class DockerStop(task.BaseTask):
    """Stops docker container with specified id"""

    async def run(self):
        command = "docker stop"
        if self.params.time is not None:
            command += f" -t {self.params.time}"
        command += f" {self.params.esc_container_id}"
        await self.sh(command)
