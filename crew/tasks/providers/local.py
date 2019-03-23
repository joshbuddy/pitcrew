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
            return self.local_context
        else:
            raise StopAsyncIteration

    def __str__(self):
        return "LocalProvider"


@task.returns("An async generator that gives a local context")
class ProvidersLocal(task.BaseTask):
    """A provider for a local context"""

    async def run(self) -> LocalProvider:
        return LocalProvider(self.context.local_context)


class ProvidersLocalTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        async for p in await self.providers.local():
            assert p == self.context.local_context
