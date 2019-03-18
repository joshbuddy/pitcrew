from crew import task


@task.returns("The name of the platform")
@task.memoize()
class Uname(task.BaseTask):
    """Returns the lowercase name of the platform"""

    async def run(self) -> str:
        return (await self.sh("uname")).strip().lower()
