import os
import atexit
import shutil
import jinja2
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

    def create_task(self, name):
        path = os.path.realpath(os.path.join(__file__, "..", "templates"))
        templateLoader = jinja2.FileSystemLoader(searchpath=path)
        templateEnv = jinja2.Environment(loader=templateLoader)
        parts = name.split(".")
        class_name = "".join(map(lambda p: p.capitalize(), parts))
        template = templateEnv.get_template("new_task.py.j2")
        rendered_task = template.render(task_class_name=class_name)
        task_path = (
            os.path.realpath(os.path.join(__file__, "..", "tasks", *parts)) + ".py"
        )
        base_path = os.path.dirname(task_path)
        os.makedirs(base_path, exist_ok=True)
        with open(task_path, "w") as fh:
            fh.write(rendered_task)

    async def __aenter__(self):
        await self.state.load()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.state.save()

    def delete_rendered_templates(self):
        shutil.rmtree(self.template_render_path, ignore_errors=True)
