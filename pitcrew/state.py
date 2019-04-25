import aiofiles
import yaml
import os


class FileState:
    def __init__(self, path):
        self.current_state = {}
        self.path = path

    async def load(self):
        if os.path.isfile(self.path):
            async with aiofiles.open(self.path, mode="r") as f:
                contents = await f.read()
                self.current_state = yaml.load(contents)

    async def save(self):
        contents = yaml.dump(self.current_state, default_flow_style=False)
        async with aiofiles.open(self.path, mode="w") as f:
            await f.write(contents)

    def get(self, key):
        return self.current_state.get(key, None)

    def set(self, key, value):
        self.current_state[key] = value


class NullState:
    async def load(self):
        pass

    async def save(self):
        pass

    def get(self, key):
        return None

    def set(self, key, value):
        pass
