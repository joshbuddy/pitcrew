import re
import os
import atexit
import shutil
import jinja2
from pitcrew.loader import Loader
from pitcrew.context import LocalContext
from pitcrew.docs import Docs
from pitcrew.test import TestRunner
from pitcrew.executor import Executor


class App:
    def __init__(self):
        self.template_render_path = os.path.join("/tmp", "crew", "templates")
        atexit.register(self.delete_rendered_templates)
        os.makedirs(self.template_render_path, exist_ok=True)
        self.loader = Loader()
        self.local_context = LocalContext(self, self.loader)

    def executor(self, *args, **kwargs):
        return Executor(*args, **kwargs)

    def load(self, task_name):
        task = self.loader.load(task_name, self.local_context)
        return task

    def docs(self):
        return Docs(self)

    def test_runner(self):
        return TestRunner(self, LocalContext(self, self.loader))

    def create_task(self, name):
        path = os.path.realpath(os.path.join(__file__, "..", "templates"))
        templateLoader = jinja2.FileSystemLoader(searchpath=path)
        templateEnv = jinja2.Environment(loader=templateLoader)
        word_parts = re.split(r"[._]", name)
        path_parts = name.split(".")
        class_name = "".join(map(lambda p: p.capitalize(), word_parts))
        template = templateEnv.get_template("new_task.py.j2")
        rendered_task = template.render(task_class_name=class_name)
        base_task_path = os.path.realpath(os.path.join(__file__, "..", "tasks"))
        task_path = os.path.join(base_task_path, *path_parts) + ".py"
        if os.path.isfile(task_path):
            raise Exception(f"there is already something in the way {task_path}")
        base_path = os.path.dirname(task_path)
        os.makedirs(base_path, exist_ok=True)
        for i in range(len(path_parts) - 1):
            potential_task_path = (
                os.path.join(base_task_path, *path_parts[0 : i + 1]) + ".py"
            )
            if os.path.isfile(potential_task_path):
                new_path = os.path.join(
                    base_task_path, *path_parts[0 : i + 1], "__init__.py"
                )
                os.rename(potential_task_path, new_path)

        with open(task_path, "w") as fh:
            fh.write(rendered_task)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def delete_rendered_templates(self):
        shutil.rmtree(self.template_render_path, ignore_errors=True)
