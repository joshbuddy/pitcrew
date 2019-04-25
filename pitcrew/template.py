import os
import uuid
from jinja2 import Template as JinjaTemplate
from pitcrew.file import File


class Template:
    def __init__(self, task, path):
        self.task = task
        self.path = path

        self.rendered_path = os.path.join(
            task.context.app.template_render_path,
            f"{uuid.uuid4()}-{os.path.basename(self.path)}",
        )

    def render(self, **kwargs) -> File:
        with open(self.rendered_path, "wb") as out:
            out.write(self.render_as_bytes(**kwargs))
        return self.task.context.app.local_context.file(self.rendered_path)

    def render_as_bytes(self, **kwargs) -> bytes:
        with open(self.path) as fh:
            template = JinjaTemplate(fh.read())
            return template.render(**kwargs).encode()
