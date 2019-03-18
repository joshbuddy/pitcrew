def ubuntu_decorator(f):
    async def wrapper(self, *args, **kwargs):
        container_id = await self.docker.run("ubuntu", detach=True, interactive=True)
        docker_ctx = self.docker_context(container_id, user="root")
        previous_context = self.context
        try:
            async with docker_ctx:
                self.context = docker_ctx
                return await f(self, *args, **kwargs)
        finally:
            self.context = previous_context

    return wrapper
