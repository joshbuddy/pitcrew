import asyncio
import getpass


class Passwords:
    def __init__(self):
        self.passwords = {}

    async def get_password(self, prompt):
        if prompt in self.passwords:
            return await self.passwords[prompt]

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self.passwords[prompt] = fut
        await loop.run_in_executor(None, self.__get_password, fut, prompt)
        return await fut

    def __get_password(self, fut, prompt):
        password = getpass.getpass(prompt=prompt)
        fut.set_result(password)
