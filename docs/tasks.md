# Tasks

## apt_get.install

Install a package using apt-get

### Arguments


- name *(str)* : The package to install
- version *(str)* : The version to install


### Returns

*(str)* The version of the installed package


<details>
<summary>Show source</summary>

```python
import re
from crew import task


@task.arg("name", type=str, desc="The package to install")
@task.arg("version", type=str, desc="The version to install")
@task.returns("The version of the installed package")
class AptgetInstall(task.BaseTask):
    """Install a package using apt-get"""

    async def verify(self) -> str:
        policy_output = await self.sh(f"apt-cache policy {self.params.esc_name}")
        m = re.search("Installed: (.*?)\n", policy_output)
        assert m, "no version found"
        installed_version = m.group(1)
        assert installed_version != "(none)", "Installed version is (none)"
        if self.params.version:
            assert installed_version == self.params.version
        else:
            saved_version = self.state_variable(self.params.name)
            requested_version = saved_version.get()
            if requested_version:
                assert requested_version == installed_version
            else:
                saved_version.set(installed_version)
        return installed_version

    async def run(self):
        saved_version = self.state_variable(self.params.name)
        version = None
        if self.params.version:
            version = self.params.version
        elif saved_version.get():
            version = saved_version.get()
        specifier = (
            f"{self.params.esc_name}={self.esc(version)}"
            if version
            else self.params.esc_name
        )
        return await self.sh(f"apt-get install -y {specifier}")

    async def available(self) -> bool:
        code, _, _ = await self.sh_with_code("which apt-get")
        return code == 0

```

</details>

## apt_get.update

Performs `apt-get update`





<details>
<summary>Show source</summary>

```python
from crew import task


class AptgetUpdate(task.BaseTask):
    """Performs `apt-get update`"""

    async def run(self):
        await self.sh("apt-get update")

```

</details>

## crew.install

Installs crew in the path specified

### Arguments


- dest *(str)* : The directory to install crew in



<details>
<summary>Show source</summary>

```python
from crew import task


@task.opt("dest", desc="The directory to install crew in", type=str, default="crew")
class CrewInstall(task.BaseTask):
    """Installs crew in the path specified"""

    async def verify(self):
        with self.cd(self.params.dest):
            await self.sh("./bin/crew --help")

    async def run(self):
        if await self.facts.system.uname() == "darwin":
            await self.install.xcode_cli()
            await self.install.homebrew()
            await self.install("git")
            await self.git.clone(
                "https://github.com/joshbuddy/crew.git", self.params.dest
            )
            with self.cd(self.params.dest):
                await self.homebrew.install("python3")
                await self.sh("python3 -m venv --clear env")
                await self.sh("env/bin/pip install -r requirements.txt")
        elif await self.facts.system.uname() == "linux":
            await self.apt_get.update()
            await self.apt_get.install("git")
            await self.apt_get.install("python3.6")
            await self.apt_get.install("python3-venv")
            await self.git.clone(
                "https://github.com/joshbuddy/crew.git", self.params.dest
            )
            with self.cd(self.params.dest):
                await self.sh("python3.6 --version")
                await self.sh("python3.6 -m venv --clear env")
                await self.sh("env/bin/pip install -r requirements.txt")
        else:
            raise Exception("cannot install on this platform")


class CrewInstallTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        with self.cd("/tmp"):
            await self.crew.install()

```

</details>

## docker.run

Runs a specific docker image

### Arguments


- image *(str)* : The image to run
- detach *(bool)* : Run container in background and print container ID
- tty *(bool)* : Allocate a pseudo-TTY
- interactive *(bool)* : Interactive mode
- publish *(list)* : Publish ports


### Returns

*(str)* The container id


<details>
<summary>Show source</summary>

```python
from crew import task


@task.arg("image", desc="The image to run", type=str)
@task.opt(
    "detach",
    desc="Run container in background and print container ID",
    default=False,
    type=bool,
)
@task.opt("tty", desc="Allocate a pseudo-TTY", default=False, type=bool)
@task.opt("interactive", desc="Interactive mode", default=False, type=bool)
@task.opt("publish", desc="Publish ports", type=list)
@task.returns("The container id")
class DockerRun(task.BaseTask):
    """Runs a specific docker image"""

    async def run(self) -> str:
        flags = []
        if self.params.detach:
            flags.append("d")
        if self.params.tty:
            flags.append("t")
        if self.params.interactive:
            flags.append("i")

        flag_string = f" -{''.join(flags)}" if flags else ""

        if self.params.publish:
            flag_string += f" -p {' '.join(self.params.publish)}"

        out = await self.sh(f"docker run{flag_string} {self.params.esc_image}")
        return out.strip()

```

</details>

## docker.stop

Stops docker container with specified id

### Arguments


- container_id *(str)* : The container id to stop
- time *(int)* : Seconds to wait for stop before killing it



<details>
<summary>Show source</summary>

```python
from crew import task


@task.arg("container_id", desc="The container id to stop", type=str)
@task.opt(
    "time", desc="Seconds to wait for stop before killing it", type=int, default=10
)
class DockerStop(task.BaseTask):
    """Stops docker container with specified id"""

    async def run(self):
        command = "docker stop"
        if self.params.time is not None:
            command += f" -t {self.params.time}"
        command += f" {self.params.esc_container_id}"
        await self.sh(command)

```

</details>

## facts.system.uname

Returns the lowercase name of the platform




### Returns

*(str)* The name of the platform


<details>
<summary>Show source</summary>

```python
from crew import task


@task.returns("The name of the platform")
@task.memoize()
class Uname(task.BaseTask):
    """Returns the lowercase name of the platform"""

    async def run(self) -> str:
        return (await self.sh("uname")).strip().lower()

```

</details>

## fs.chmod

Changes the file mode of the specified path

### Arguments


- path *(str)* : The path to change the mode of
- mode *(str)* : The mode



<details>
<summary>Show source</summary>

```python
from crew import task


@task.arg("path", desc="The path to change the mode of", type=str)
@task.arg("mode", desc="The mode", type=str)
@task.returns("The bytes of the file")
class FsChmod(task.BaseTask):
    """Changes the file mode of the specified path"""

    async def run(self):
        return await self.sh(f"chmod {self.params.esc_mode} {self.params.esc_path}")


class FsChmodTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        with self.cd("/tmp"):
            await self.fs.touch("some-file")
            await self.fs.chmod("some-file", "644")
            assert (await self.fs.stat("some-file")).mode == "100644"
            await self.fs.chmod("some-file", "o+x")
            assert (await self.fs.stat("some-file")).mode == "100645"

```

</details>

## fs.chown

Changes the file mode of the specified path

### Arguments


- path *(str)* : The path to change the mode of
- owner *(str)* : The owner
- group *(str)* : The owner



<details>
<summary>Show source</summary>

```python
from crew import task


@task.arg("path", desc="The path to change the mode of", type=str)
@task.arg("owner", desc="The owner", type=str)
@task.opt("group", desc="The owner", type=str)
@task.returns("The bytes of the file")
class FsChown(task.BaseTask):
    """Changes the file mode of the specified path"""

    async def run(self):
        owner_str = self.params.owner
        if self.params.group:
            owner_str += f":{self.params.group}"
        return await self.sh(f"chown {self.esc(owner_str)} {self.params.esc_path}")

```

</details>

## fs.digests.md5

Gets md5 digest of path

### Arguments


- path *(str)* : The path of the file to digest


### Returns

*(str)* The md5 digest in hexadecimal


<details>
<summary>Show source</summary>

```python
import hashlib
from crew import task


@task.arg("path", desc="The path of the file to digest", type=str)
@task.returns("The md5 digest in hexadecimal")
class FsDigestsMd5(task.BaseTask):
    """Gets md5 digest of path"""

    async def run(self) -> str:
        platform = await self.facts.system.uname()
        if platform == "darwin":
            out = await self.sh(f"md5 {self.params.esc_path}")
            return out.strip().split(" ")[-1]
        elif platform == "linux":
            out = await self.sh(f"md5sum {self.params.esc_path}")
            return out.split(" ")[0]
        else:
            raise Exception("not supported")


class FsDigestsMd5Test(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        content = b"Some delicious bytes"
        await self.fs.write("/tmp/some-file", content)
        expected_digest = hashlib.md5(content).hexdigest()
        actual_digest = await self.fs.digests.md5("/tmp/some-file")
        assert expected_digest == actual_digest, "digests are not equal"

```

</details>

## fs.digests.sha256

Gets sha256 digest of path

### Arguments


- path *(str)* : The path of the file to digest


### Returns

*(str)* The sha256 digest in hexadecimal


<details>
<summary>Show source</summary>

```python
import hashlib
from crew import task


@task.arg("path", desc="The path of the file to digest", type=str)
@task.returns("The sha256 digest in hexadecimal")
class FsDigestsSha256(task.BaseTask):
    """Gets sha256 digest of path"""

    async def run(self) -> str:
        platform = await self.facts.system.uname()
        if platform == "darwin":
            out = await self.sh(f"shasum -a256 {self.params.esc_path}")
            return out.split(" ")[0]
        elif platform == "linux":
            out = await self.sh(f"sha256sum {self.params.esc_path}")
            return out.split(" ")[0]
        else:
            raise Exception("not supported")


class FsDigestsSha256Test(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        content = b"Some delicious bytes"
        await self.fs.write("/tmp/some-file", content)
        expected_digest = hashlib.sha256(content).hexdigest()
        actual_digest = await self.fs.digests.sha256("/tmp/some-file")
        assert expected_digest == actual_digest, "digests are not equal"

```

</details>

## fs.is_directory

Checks if the path is a directory

### Arguments


- path *(str)* : The path to check


### Returns

*(bool)* Indicates if target path is a directory


<details>
<summary>Show source</summary>

```python
from crew import task


@task.arg("path", desc="The path to check")
@task.returns("Indicates if target path is a directory")
class FsIsDirectory(task.BaseTask):
    """Checks if the path is a directory"""

    async def run(self) -> bool:
        code, _, _ = await self.sh_with_code(f"test -d {self.params.esc_path}")
        return code == 0

```

</details>

## fs.is_file

Checks if the path is a directory

### Arguments


- path *(str)* : The path to check


### Returns

*(bool)* Indicates if target path is a directory


<details>
<summary>Show source</summary>

```python
from crew import task


@task.arg("path", desc="The path to check")
@task.returns("Indicates if target path is a directory")
class FsIsFile(task.BaseTask):
    """Checks if the path is a directory"""

    async def run(self) -> bool:
        code, _, _ = await self.sh_with_code(f"test -f {self.params.esc_path}")
        return code == 0

```

</details>

## fs.read

Read value of path into bytes

### Arguments


- path *(str)* : The file to read


### Returns

*(bytes)* The bytes of the file


<details>
<summary>Show source</summary>

```python
from crew import task


@task.arg("path", desc="The file to read", type=str)
@task.returns("The bytes of the file")
class FsRead(task.BaseTask):
    """Read value of path into bytes"""

    async def run(self) -> bytes:
        code, out, err = await self.sh_with_code(f"cat {self.params.esc_path}")
        assert code == 0, "exitcode was not zero"
        return out

```

</details>

## fs.stat

Get stat info for path

### Arguments


- path *(str)* : The path of the file to stat


### Returns

*(Stat)* the stat object for the file


<details>
<summary>Show source</summary>

```python
from crew import task


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

```

</details>

## fs.touch

Touches a file

### Arguments


- path *(str)* : The path to change the mode of



<details>
<summary>Show source</summary>

```python
from crew import task


@task.arg("path", desc="The path to change the mode of", type=str)
class FsTouch(task.BaseTask):
    """Touches a file"""

    async def run(self):
        return await self.sh(f"touch {self.params.esc_path}")

```

</details>

## fs.write

Write bytes to a file

### Arguments


- path *(str)* : The path of the file to write to
- content *(bytes)* : The contents to write



<details>
<summary>Show source</summary>

```python
import base64
import hashlib
from crew import task


@task.arg("path", type=str, desc="The path of the file to write to")
@task.arg("content", type=bytes, desc="The contents to write")
class FsWrite(task.BaseTask):
    """Write bytes to a file"""

    async def verify(self):
        stat = await self.fs.stat(self.params.path)
        self.assert_equals(len(self.params.content), stat.size)
        expected_digest = hashlib.sha256(self.params.content).hexdigest()
        actual_digest = await self.fs.digests.sha256(self.params.path)
        self.assert_equals(actual_digest, expected_digest)

    async def run(self):
        await self.sh(
            f"echo {self.esc(base64.b64encode(self.params.content).decode())} | base64 --decode | tee {self.params.esc_path} > /dev/null"
        )

```

</details>

## git.clone

Installs a package, optionally allowing the version number to specified.

This task defers exection to package-manager specific installation tasks, such as
homebrew or apt-get.
    

### Arguments


- url *(str)* : The url to clone
- destination *(str)* : The destination



<details>
<summary>Show source</summary>

```python
import os
from crew import task


@task.arg("url", desc="The url to clone", type=str)
@task.arg("destination", desc="The destination", type=str)
class GitClone(task.BaseTask):
    """Installs a package, optionally allowing the version number to specified.

This task defers exection to package-manager specific installation tasks, such as
homebrew or apt-get.
    """

    async def verify(self):
        git_config = await self.fs.read(
            os.path.join(self.params.destination, ".git", "config")
        )
        assert self.params.url in git_config.decode()

    async def run(self):
        command = f"git clone {self.params.esc_url} {self.params.esc_destination}"
        await self.sh(command)

```

</details>

## homebrew.install

Read value of path into bytes

### Arguments


- name *(str)* : Package to install


### Returns

*(str)* the version installed


<details>
<summary>Show source</summary>

```python
from crew import task


@task.arg("name", type=str, desc="Package to install")
@task.returns("the version installed")
class HomebrewInstall(task.BaseTask):
    """Read value of path into bytes"""

    async def verify(self) -> str:
        code, out, err = await self.sh_with_code(
            f"brew ls --versions {self.params.esc_name}"
        )
        lines = out.decode().strip().split("\n")
        if lines != [""]:
            for line in lines:
                _, version = line.split(" ", 1)
                return version
        assert False, f"no version found for {self.params.name}"

    async def run(self):
        await self.sh(f"brew install {self.params.esc_name}")

    async def available(self) -> bool:
        code, _, _ = await self.sh_with_code("which brew")
        return code == 0

```

</details>

## install.homebrew

Ensures xcode is installed





<details>
<summary>Show source</summary>

```python
from crew import task


class InstallHomebrew(task.BaseTask):
    """Ensures xcode is installed"""

    async def verify(self):
        assert await self.sh("which brew")

    async def run(self):
        await self.sh(
            '/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'
        )

```

</details>

## install.xcode_cli

Ensures xcode is installed





<details>
<summary>Show source</summary>

```python
from crew import task


class InstallXcodeCli(task.BaseTask):
    """Ensures xcode is installed"""

    async def verify(self):
        assert await self.fs.is_directory("/Library/Developer/CommandLineTools")

    async def run(self):
        await self.sh("xcode-select --install")
        await self.poll(self.verify)

```

</details>

