from crew import task


class AptgetUpdate(task.BaseTask):
    """Performs `apt-get update`"""

    async def run(self):
        await self.sh("apt-get update")
