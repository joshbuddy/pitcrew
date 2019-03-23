import asyncio


class ExecutorResult:
    def __init__(self):
        self.contexts = {}
        self.passed = {}
        self.failed = {}


class Executor:
    def __init__(self, provider, concurrency=None):
        self.provider = provider
        self.concurrency = concurrency
        if self.concurrency:
            self.barrier = asyncio.Semaphore(count=self.concurrency)
        else:
            self.barrier = None

    async def run_task(self, task, *args, **kwargs) -> ExecutorResult:
        async def execute_task(ctx, *args, **kwargs):
            return await task.invoke_with_context(ctx, *args, **kwargs)

        return await self.invoke(execute_task, *args, **kwargs)

    async def invoke(self, fn, *args, **kwargs) -> ExecutorResult:
        results = ExecutorResult()
        async for context in self.provider:
            if self.barrier:
                self.barrier.acquire()
            try:
                async with context:
                    results.contexts[context.descriptor()] = context
                    try:
                        result = await context.invoke(fn, *args, **kwargs)
                        results.passed[context.descriptor()] = result
                    except Exception as e:
                        results.failed[context.descriptor()] = e
                        raise e
            finally:
                if self.barrier:
                    self.barrier.release()
        return results
