import os
import uuid
from jinja2 import Template as JinjaTemplate
from crew.file import File


class Template:
    def __init__(self, task, path):
        self.task = task
        self.path = path

        self.rendered_path = os.path.join(
            task.context.app.template_render_path,
            f"{uuid.uuid4()}-{os.path.basename(self.path)}",
        )

    def render(self, **kwargs) -> File:
        with open(self.path) as fh:
            template = JinjaTemplate(fh.read())
            result = template.render(**kwargs)
            with open(self.rendered_path, "w") as outh:
                outh.write(result)
        return self.task.context.app.local_context.file(self.rendered_path)
