from crew import task


class LocalProvider:
    def __init__(self, local_context):
        self.returned = False
        self.local_context = local_context

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.returned:
            self.returned = True
            async with self.local_context:
                return self.local_context
        else:
            raise StopAsyncIteration

    def __str__(self):
        return "LocalProvider"


@task.returns("Describe the return value")
class ProvidersLocal(task.BaseTask):
    """The description of the task"""

    async def run(self) -> LocalProvider:
        return LocalProvider(self.context.local_context)


class ProvidersLocalTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        async for p in await self.providers.local():
            assert p == self.context.local_context
