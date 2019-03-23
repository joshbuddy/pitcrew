from crew import task


class DockerProvider:
    def __init__(self, context, container_ids):
        self.context = context
        self.container_ids = container_ids
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index == len(self.container_ids):
            raise StopAsyncIteration
        docker_ctx = self.context.docker_context(
            container_id=self.container_ids[self.index]
        )
        self.index += 1
        return docker_ctx

    def __str__(self):
        return f"DockerProvider(container_ids={self.container_ids})"


@task.returns("An async generator that gives ssh contexts")
@task.arg("container_ids", type=list, desc="The container ids to use")
class ProvidersDocker(task.BaseTask):
    """A provider for ssh contexts"""

    async def run(self) -> DockerProvider:
        return DockerProvider(self.context, self.params.container_ids)
