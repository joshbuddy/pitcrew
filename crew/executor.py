import asyncio


class WorkItem:
    def __init__(self, context, fn, args, kwargs):
        self.context = context
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


class ExecutionResult:
    def __init__(self, context, result, exception):
        self.context = context
        self.result = result
        self.exception = exception


class ResultsList:
    def __init__(self):
        self.results = []
        self.passed = []
        self.failed = []
        self.errored = []

    def append(self, result):
        self.results.append(result)

        if result.exception and isinstance(result.exception, AssertionError):
            self.failed.append(result)
        elif result.exception:
            self.errored.append(result)
        else:
            self.passed.append(result)


class Executor:
    def __init__(self, provider, concurrency=100):
        self.provider = provider
        self.concurrency = concurrency
        self.queue = asyncio.Queue(maxsize=self.concurrency)
        self.results = ResultsList()
        self.workers = []

    async def run_task(self, task, *args, **kwargs) -> ResultsList:
        async def execute_task(ctx, *args, **kwargs):
            return await task.invoke_with_context(ctx, *args, **kwargs)

        return await self.invoke(execute_task, *args, **kwargs)

    async def invoke(self, fn, *args, **kwargs) -> ResultsList:
        enqueuer_future = asyncio.ensure_future(
            self._start_provider_enquerer(fn, *args, **kwargs)
        )
        await asyncio.wait_for(enqueuer_future, None)
        await self.queue.join()
        return self.results

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        for w in self.workers:
            w.cancel()

        for w in asyncio.as_completed(self.workers):
            await w

    def _start_worker(self):
        self.workers.append(asyncio.ensure_future(self._worker_loop()))

    async def _worker_loop(self):
        try:
            while True:
                item = await self.queue.get()
                try:
                    async with item.context:
                        try:
                            result = await item.context.invoke(
                                item.fn, *item.args, **item.kwargs
                            )
                            self.results.append(
                                ExecutionResult(item.context, result, None)
                            )
                        except Exception as e:
                            self.results.append(ExecutionResult(item.context, None, e))
                except Exception as e:
                    self.results.append(ExecutionResult(item.context, None, e))
                finally:
                    self.queue.task_done()
        except asyncio.CancelledError:
            pass

    async def _start_provider_enquerer(self, fn, *args, **kwargs):
        async for context in self.provider:
            await self.queue.put(WorkItem(context, fn, args, kwargs))
            self._start_worker()
