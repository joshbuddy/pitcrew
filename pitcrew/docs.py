import os
import jinja2


class Docs:
    def __init__(self, app):
        self.app = app
        self.undoced_tasks = []

    def generate(self):
        path = os.path.realpath(os.path.join(__file__, "..", "templates"))
        templateLoader = jinja2.FileSystemLoader(searchpath=path)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template("task.md.j2")
        tasks = []
        for task in self.app.loader.each_task():
            if task.nodoc:
                continue
            desc = task.desc()
            if not desc:
                self.undoced_tasks.append(task)
            tasks.append(template.render(task=task, desc=desc))
        big_template = templateEnv.get_template("tasks.md.j2")
        return big_template.render(tasks=tasks)

    def check(self):
        self.undoced_tasks = []
        self.generate()
        if self.undoced_tasks:
            tasks = ", ".join(map(lambda t: t.task_name, self.undoced_tasks))
            raise Exception(f"there are tasks undoced {tasks}")
