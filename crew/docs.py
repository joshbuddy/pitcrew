import os
import jinja2


class Docs:
    def __init__(self, app):
        self.app = app

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
            tasks.append(template.render(task=task, desc=desc))
        big_template = templateEnv.get_template("tasks.md.j2")
        return big_template.render(tasks=tasks)
