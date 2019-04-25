from pitcrew.logger import logger


class TestRunner:
    def __init__(self, app, context):
        self.app = app
        self.context = context

    async def run(self, prefix=None):
        for task in self.app.loader.each_task():
            if prefix and not task.task_name.startswith(prefix):
                continue
            for test_cls in task.tests:
                test = test_cls(self.context)
                for name, val in test_cls.__dict__.items():
                    if name.startswith("test_"):
                        test_method = getattr(test, name)
                        with logger.with_test(task, name):
                            await test_method()
