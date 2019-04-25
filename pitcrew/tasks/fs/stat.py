from pitcrew import task


class Stat:
    inode: int
    mode: str
    user_id: int
    group_id: int
    size: int
    access_time: int
    modify_time: int
    create_time: int
    block_size: int
    blocks: int

    def __str__(self):
        return f"inode={self.inode} mode={self.mode} user_id={self.user_id} group_id={self.group_id} size={self.size} access_time={self.access_time} modify_time={self.modify_time} create_time={self.create_time} block_size={self.block_size} blocks={self.blocks}"


@task.arg("path", desc="The path of the file to stat", type=str)
@task.returns("the stat object for the file")
class FsStat(task.BaseTask):

    """Get stat info for path"""

    async def run(self) -> Stat:
        stat = Stat()
        platform = await self.facts.system.uname()
        if platform == "darwin":
            out = await self.sh(
                f'stat -f "%i %p %u %g %z %a %m %c %k %b" {self.params.esc_path}'
            )
            parts = out.strip().split(" ", 9)
        elif platform == "linux":
            out = await self.sh(
                f'stat --format "%i %f %u %g %s %X %Y %W %B %b" {self.params.esc_path}'
            )
            parts = out.strip().split(" ", 9)
        else:
            raise Exception(f"Can't support {platform}")
        stat.inode = int(parts[0])
        stat.mode = "{0:o}".format(int(parts[1], 16))
        stat.user_id = int(parts[2])
        stat.group_id = int(parts[3])
        stat.size = int(parts[4])
        stat.access_time = int(parts[5])
        stat.modify_time = int(parts[6])
        stat.create_time = int(parts[7])
        stat.block_size = int(parts[8])
        stat.blocks = int(parts[9])
        return stat


class FsStatTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        await self.fs.write("/tmp/some-file", b"Some delicious bytes")
        stat = await self.fs.stat("/tmp/some-file")
        assert stat.size == 20, "size is incorrect"
