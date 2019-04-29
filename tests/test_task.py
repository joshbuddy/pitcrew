from pitcrew import task
import aiounittest


class TestTask(aiounittest.AsyncTestCase):
    async def test_normal_arg(self):
        @task.arg("normal")
        class Task(task.BaseTask):
            async def run(self):
                pass

        task_instance = Task()
        await task_instance.invoke(normal="arg")

    async def test_normal_args(self):
        @task.arg("one")
        @task.arg("two")
        @task.arg("three")
        class Task(task.BaseTask):
            async def run(self):
                assert self.params.one == "one"
                assert self.params.two == "two"
                assert self.params.three == "three"

        task_instance = Task()
        await task_instance.invoke("one", "two", "three")

    async def test_normal_args_via_keyword(self):
        @task.arg("one")
        @task.arg("two")
        @task.arg("three")
        class Task(task.BaseTask):
            async def run(self):
                assert self.params.one == "one"
                assert self.params.two == "two"
                assert self.params.three == "three"

        task_instance = Task()
        await task_instance.invoke(one="one", two="two", three="three")

    async def test_normal_kwargs(self):
        @task.opt("optional")
        class Task(task.BaseTask):
            async def run(self):
                assert self.params.optional is None

        task_instance = Task()
        await task_instance.invoke()

    async def test_extra_kwargs(self):
        class Task(task.BaseTask):
            async def run(self):
                pass

        task_instance = Task()
        with self.assertRaises(TypeError):
            await task_instance.invoke(extra="arg")

    async def test_extra_args(self):
        @task.arg("one")
        class Task(task.BaseTask):
            async def run(self):
                pass

        task_instance = Task()
        with self.assertRaises(TypeError):
            await task_instance.invoke("asd", "qwe")

    async def test_varargs(self):
        @task.varargs("one", type=str)
        class Task(task.BaseTask):
            async def run(self):
                assert self.params.one == ["one", "two", "three"]

        task_instance = Task()
        await task_instance.invoke("one", "two", "three")
