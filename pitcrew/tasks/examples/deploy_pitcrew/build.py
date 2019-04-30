import os
import re
import asyncio
from pitcrew import task


class Build(task.BaseTask):
    """Builds the website in the `out` directory."""

    async def run(self):
        # create docs for python stuff
        await self.sh("make docs")
        # create task specific docs
        await self.sh("crew docs")
        # re-create out directory
        await self.sh("rm -rf out")
        await self.sh("mkdir out")
        # copy our css
        await self.task_file("water.css").copy_to(self.file("out/water.css"))

        docs = []
        files = await self.fs.list("docs")
        for f in files:
            name = f.split("/")[-1]
            target = f"out/docs/{os.path.splitext(name)[0]}.html"
            docs.append(self.generate_doc(f"docs/{f}", target))
        docs.append(self.generate_doc("README.md", "out/index.html"))
        await asyncio.gather(*docs)

    async def generate_doc(self, source, target):
        out = await self.sh(
            f"env/bin/python -m markdown2 -x fenced-code-blocks -x header-ids {source}"
        )
        out = re.sub(r"\.md", ".html", out)
        await self.sh(f"mkdir -p {self.esc(os.path.split(target)[0])}")
        page = self.template("doc.html.j2").render_as_bytes(body=out)
        await self.fs.write(target, page)
