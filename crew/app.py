import os
import atexit
import shutil
from crew.loader import Loader
from crew.state import FileState, NullState
from crew.context import LocalContext
from crew.docs import Docs
from crew.test import TestRunner


class App:
    def __init__(self):
        self.template_render_path = os.path.join("/tmp", "crew", "templates")
        atexit.register(self.delete_rendered_templates)
        os.makedirs(self.template_render_path, exist_ok=True)
        self.state = FileState(os.path.join(os.getcwd(), "state.yml"))
        self.loader = Loader()
        self.local_context = LocalContext(self, self.loader, self.state)

    def load(self, task_name):
        task = self.loader.load(task_name, self.local_context)
        return task

    def docs(self):
        return Docs(self)

    def test_runner(self):
        return TestRunner(self, LocalContext(self, self.loader, NullState()))

    async def __aenter__(self):
        await self.state.load()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.state.save()

    def delete_rendered_templates(self):
        shutil.rmtree(self.template_render_path)
