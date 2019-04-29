# Tasks

## apt_get.install

Install a package using apt-get

### Arguments


- name *(str)* : The package to install


### Returns

*(str)* The version of the installed package


<details>
<summary>Show source</summary>

```python
import re
from pitcrew import task


@task.arg("name", type=str, desc="The package to install")
@task.returns("The version of the installed package")
class AptgetInstall(task.BaseTask):
    """Install a package using apt-get"""

    async def verify(self) -> str:
        policy_output = await self.sh(f"apt-cache policy {self.params.esc_name}")
        m = re.search("Installed: (.*?)\n", policy_output)
        assert m, "no version found"
        installed_version = m.group(1)
        assert installed_version != "(none)", "Installed version is (none)"
        return installed_version

    async def run(self):
        return await self.sh(f"apt-get install -y {self.params.esc_name}")

    async def available(self) -> bool:
        code, _, _ = await self.sh_with_code("which apt-get")
        return code == 0

```

</details>

-------------------------------------------------

## apt_get.update

Performs `apt-get update`





<details>
<summary>Show source</summary>

```python
from pitcrew import task


class AptgetUpdate(task.BaseTask):
    """Performs `apt-get update`"""

    async def run(self):
        await self.sh("apt-get update")

```

</details>

-------------------------------------------------

## crew.install

Installs crew in the path specified

### Arguments


- dest *(str)* : The directory to install crew in



<details>
<summary>Show source</summary>

```python
from pitcrew import task


@task.opt("dest", desc="The directory to install crew in", type=str, default="pitcrew")
class CrewInstall(task.BaseTask):
    """Installs crew in the path specified"""

    async def verify(self):
        with self.cd(self.params.dest):
            await self.sh("./env/bin/crew --help")

    async def run(self):
        platform = await self.facts.system.uname()
        if platform == "darwin":
            await self.install.xcode_cli()
            await self.install.homebrew()
            await self.install("git")
            await self.git.clone(
                "https://github.com/joshbuddy/pitcrew.git", self.params.dest
            )
            with self.cd(self.params.dest):
                await self.homebrew.install("python3")
                await self.sh("python3 -m venv --clear env")
                await self.sh("env/bin/pip install -e .")
        elif platform == "linux":
            if await self.sh_ok("which apt-get"):
                await self.apt_get.update()
                await self.apt_get.install("apt-utils")
                await self.apt_get.install("git")
                await self.apt_get.install("python3.7")
                await self.apt_get.install("python3.7-dev")
                await self.apt_get.install("python3.7-venv")
                await self.sh(
                    "apt-get install -y python3.7-distutils",
                    env={"DEBIAN_FRONTEND": "noninteractive"},
                )
            else:
                raise Exception(f"cannot install on this platform {platform}")

            await self.git.clone(
                "https://github.com/joshbuddy/pitcrew.git", self.params.dest
            )
            with self.cd(self.params.dest):
                await self.sh("python3.7 -m venv env")
                await self.sh("env/bin/pip install --upgrade pip wheel")
                await self.sh("env/bin/pip install -e .")

        else:
            raise Exception(f"cannot install on this platform {platform}")


class CrewInstallTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        with self.cd("/tmp"):
            # put this in to test the local copy you've got
            await self.local_context.file(".").copy_to(self.file("/tmp/pitcrew"))
            await self.sh("rm -rf /tmp/pitcrew/env")
            await self.fs.write(
                "/tmp/pitcrew/.git/config",
                b"""[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
    logallrefupdates = true
    ignorecase = true
    precomposeunicode = true
[remote "origin"]
    url = https://github.com/joshbuddy/pitcrew.git
    fetch = +refs/heads/*:refs/remotes/origin/*
""",
            )
            await self.crew.install()

```

</details>

-------------------------------------------------

## crew.release

This creates a release for crew

### Arguments


- version *(str)* : The version to release
- name *(str)* : The name of the release



<details>
<summary>Show source</summary>

```python
import re
from pitcrew import task


@task.arg("version", desc="The version to release", type=str)
@task.arg("name", desc="The name of the release", type=str)
class CrewRelease(task.BaseTask):
    """This creates a release for crew"""

    async def run(self):
        current_branch = (await self.sh("git rev-parse --abbrev-ref HEAD")).strip()
        assert "master" == current_branch, "not on master"
        assert re.match(r"\d+\.\d+\.\d+", self.params.version)
        await self.sh("mkdir -p pkg")
        await self.run_all(
            self.crew.release.darwin(self.params.version),
            self.crew.release.linux(self.params.version),
        )
        await self.sh(
            f"env/bin/githubrelease release joshbuddy/pitcrew create {self.params.version} --publish --name {self.params.esc_name} {self.esc('pkg/*')}"
        )

```

</details>

-------------------------------------------------

## crew.release.darwin

This creates a PyInstaller build for crew on Darwin

### Arguments


- version *(str)* : The version to release



<details>
<summary>Show source</summary>

```python
from pitcrew import task


@task.arg("version", desc="The version to release", type=str)
class CrewBuildDarwin(task.BaseTask):
    """This creates a PyInstaller build for crew on Darwin"""

    async def run(self):
        assert await self.facts.system.uname() == "darwin"
        await self.sh("make build")
        target = f"pkg/crew-{self.params.version}-darwin"
        await self.sh(f"cp dist/crew {target}")

```

</details>

-------------------------------------------------

## crew.release.linux

This creates a PyInstaller build for crew on Linux

### Arguments


- version *(str)* : The version to release



<details>
<summary>Show source</summary>

```python
from pitcrew import task


@task.arg("version", desc="The version to release", type=str)
class CrewBuildLinux(task.BaseTask):
    """This creates a PyInstaller build for crew on Linux"""

    async def run(self):
        container_id = await self.docker.run("ubuntu", detach=True, interactive=True)
        docker_ctx = self.docker_context(container_id, user="root")

        async with docker_ctx:
            assert (
                await docker_ctx.facts.system.uname() == "linux"
            ), "the platform is not linux!"
            await self.file(".").copy_to(docker_ctx.file("/tmp/crew"))
            await docker_ctx.apt_get.update()
            await docker_ctx.apt_get.install("python3.6")
            await docker_ctx.apt_get.install("python3.6-dev")
            await docker_ctx.apt_get.install("python3-venv")
            await docker_ctx.apt_get.install("build-essential")
            with docker_ctx.cd("/tmp/crew"):
                await docker_ctx.sh("python3.6 -m venv --clear env")
                await docker_ctx.sh("env/bin/pip install -r requirements.txt")
                await docker_ctx.sh("make build")
                target = f"pkg/crew-{self.params.version}-linux"
                await docker_ctx.file("/tmp/crew/dist/crew").copy_to(self.file(target))

```

</details>

-------------------------------------------------

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
from pitcrew import task


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

-------------------------------------------------

## docker.stop

Stops docker container with specified id

### Arguments


- container_id *(str)* : The container id to stop
- time *(int)* : Seconds to wait for stop before killing it



<details>
<summary>Show source</summary>

```python
from pitcrew import task


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

-------------------------------------------------

## ensure.aws.route53.has_records

Ensure route53 has the set of records

### Arguments


- zone_id *(str)* : The zone id to operate on
- records *(list)* : A list of records to ensure are set



<details>
<summary>Show source</summary>

```python
import json
import asyncio
from pitcrew import task


@task.arg("zone_id", desc="The zone id to operate on", type=str)
@task.arg("records", desc="A list of records to ensure are set", type=list)
class HasRecords(task.BaseTask):
    """Ensure route53 has the set of records"""

    async def verify(self):
        json_out = await self.sh(
            f"aws route53 list-resource-record-sets --hosted-zone-id {self.params.esc_zone_id}"
        )
        out = json.loads(json_out)
        existing_record_sets = out["ResourceRecordSets"]
        for record in self.params.records:
            assert record in existing_record_sets, "cannot find record"

    async def run(self):
        changes = map(
            lambda c: {"Action": "UPSERT", "ResourceRecordSet": c}, self.params.records
        )
        change_batch = {"Changes": list(changes)}
        change_id = json.loads(
            await self.sh(
                f"aws route53 change-resource-record-sets --hosted-zone-id {self.params.esc_zone_id} --change-batch {self.esc(json.dumps(change_batch))}"
            )
        )["ChangeInfo"]["Id"]
        while (
            json.loads(
                await self.sh(f"aws route53 get-change --id {self.esc(change_id)}")
            )["ChangeInfo"]["Status"]
            == "PENDING"
        ):
            await asyncio.sleep(5)

```

</details>

-------------------------------------------------

## examples.deploy_pitcrew

This example builds and deploys pitcrew.io. It uses s3, cloudfront and acm to deploy
    this website using ssl. 





<details>
<summary>Show source</summary>

```python
import json
import asyncio
from pitcrew import task
from uuid import uuid4


class DeployPitcrew(task.BaseTask):
    """This example builds and deploys pitcrew.io. It uses s3, cloudfront and acm to deploy
    this website using ssl. """

    async def run(self):
        await self.sh("aws s3api create-bucket --bucket pitcrew-site")
        await self.run_all(self.setup_aws(), self.build_and_sync())

    async def setup_aws(self):
        zones = json.loads(await self.sh("aws route53 list-hosted-zones"))[
            "HostedZones"
        ]
        zone_id = None
        for zone in zones:
            if zone["Name"] == "pitcrew.io.":
                zone_id = zone["Id"]
                break

        assert zone_id, "no zone_id found for pitcrew.io"

        cert_arn = await self.setup_acm(zone_id)
        cf_id = await self.setup_cloudfront(zone_id, cert_arn)
        dist = json.loads(
            await self.sh(f"aws cloudfront get-distribution --id {self.esc(cf_id)}")
        )["Distribution"]
        domain_name = dist["DomainName"]

        await self.ensure.aws.route53.has_records(
            zone_id,
            [
                {
                    "Name": "pitcrew.io.",
                    "Type": "A",
                    "AliasTarget": {
                        "HostedZoneId": "Z2FDTNDATAQYW2",
                        "DNSName": f"{domain_name}.",
                        "EvaluateTargetHealth": False,
                    },
                },
                {
                    "Name": "pitcrew.io.",
                    "Type": "AAAA",
                    "AliasTarget": {
                        "HostedZoneId": "Z2FDTNDATAQYW2",
                        "DNSName": f"{domain_name}.",
                        "EvaluateTargetHealth": False,
                    },
                },
                {
                    "Name": "www.pitcrew.io.",
                    "Type": "CNAME",
                    "TTL": 300,
                    "ResourceRecords": [{"Value": domain_name}],
                },
            ],
        )

    async def setup_acm(self, zone_id):
        certs = json.loads(
            await self.sh("aws acm list-certificates --certificate-statuses ISSUED")
        )["CertificateSummaryList"]
        for cert in certs:
            if cert["DomainName"] == "pitcrew.io":
                return cert["CertificateArn"]

        arn = json.loads(
            await self.sh(
                f"aws acm request-certificate --domain-name pitcrew.io --validation-method DNS --subject-alternative-names {self.esc('*.pitcrew.io')}"
            )
        )["CertificateArn"]
        cert_description = json.loads(
            await self.sh(
                f"aws acm describe-certificate --certificate-arn {self.esc(arn)}"
            )
        )

        validation = cert_description["Certificate"]["DomainValidationOptions"][0]
        changes = []
        changes.append(
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": validation["ResourceRecord"]["Name"],
                    "Type": validation["ResourceRecord"]["Type"],
                    "TTL": 60,
                    "ResourceRecords": [
                        {"Value": validation["ResourceRecord"]["Value"]}
                    ],
                },
            }
        )

        change_batch = {"Changes": list(changes)}
        change_id = json.loads(
            await self.sh(
                f"aws route53 change-resource-record-sets --hosted-zone-id {self.esc(zone_id)} --change-batch {self.esc(json.dumps(change_batch))}"
            )
        )["ChangeInfo"]["Id"]
        while (
            json.loads(
                await self.sh(f"aws route53 get-change --id {self.esc(change_id)}")
            )["ChangeInfo"]["Status"]
            == "PENDING"
        ):
            await asyncio.sleep(5)

        await self.sh(
            f"aws acm wait certificate-validated --certificate-arn {self.esc(arn)}"
        )
        return arn

    async def setup_cloudfront(self, zone_id, cert_arn) -> str:
        s3_origin = "pitcrew-site.s3.amazonaws.com"

        out = json.loads(await self.sh(f"aws cloudfront list-distributions"))
        items = out["DistributionList"]["Items"]
        cf_id = None
        config = {
            "DefaultRootObject": "index.html",
            "Aliases": {"Quantity": 2, "Items": ["pitcrew.io", "www.pitcrew.io"]},
            "Origins": {
                "Quantity": 1,
                "Items": [
                    {
                        "Id": "pitcrew-origin",
                        "DomainName": s3_origin,
                        "S3OriginConfig": {"OriginAccessIdentity": ""},
                    }
                ],
            },
            "DefaultCacheBehavior": {
                "TargetOriginId": "pitcrew-origin",
                "ForwardedValues": {
                    "QueryString": True,
                    "Cookies": {"Forward": "none"},
                },
                "TrustedSigners": {"Enabled": False, "Quantity": 0},
                "ViewerProtocolPolicy": "redirect-to-https",
                "MinTTL": 180,
            },
            "CallerReference": str(uuid4()),
            "Comment": "Created by crew",
            "Enabled": True,
            "ViewerCertificate": {
                "ACMCertificateArn": cert_arn,
                "SSLSupportMethod": "sni-only",
            },
        }
        for dist in items:
            if dist["Origins"]["Items"][0]["DomainName"] == s3_origin:
                return dist["Id"]

        out = json.loads(
            await self.sh(
                f"aws cloudfront create-distribution --distribution-config {self.esc(json.dumps(config))}"
            )
        )
        cf_id = out["Distribution"]["Id"]
        await self.sh(f"aws cloudfront wait distribution-deployed --id {cf_id}")
        return cf_id

    async def build_and_sync(self):
        await self.examples.deploy_pitcrew.build()
        await self.sh("aws s3 sync --acl public-read out/ s3://pitcrew-site/")

```

</details>

-------------------------------------------------

## examples.deploy_pitcrew.build

Builds the website in the `out` directory.





<details>
<summary>Show source</summary>

```python
import os
import re
from pitcrew import task


class Build(task.BaseTask):
    """Builds the website in the `out` directory."""

    async def run(self):
        await self.sh("crew docs")
        await self.sh("rm -rf out")
        await self.sh("mkdir out")
        await self.task_file("water.css").copy_to(self.file("out/water.css"))

        docs = []
        files = await self.fs.list("docs")
        for f in files:
            name = f.split("/")[-1]
            target = f"out/docs/{os.path.splitext(name)[0]}.html"
            docs.append(self.generate_doc(f"docs/{f}", target))
        docs.append(self.generate_doc("README.md", "out/index.html"))
        await self.run_all(*docs)

    async def generate_doc(self, source, target):
        out = await self.sh(
            f"env/bin/python -m markdown2 -x fenced-code-blocks -x header-ids {source}"
        )
        out = re.sub(r"\.md", ".html", out)
        await self.sh(f"mkdir -p {self.esc(os.path.split(target)[0])}")
        page = self.template("doc.html.j2").render_as_bytes(body=out)
        await self.fs.write(target, page)

```

</details>

-------------------------------------------------

## facts.system.uname

Returns the lowercase name of the platform




### Returns

*(str)* The name of the platform


<details>
<summary>Show source</summary>

```python
from pitcrew import task


@task.returns("The name of the platform")
@task.memoize()
class Uname(task.BaseTask):
    """Returns the lowercase name of the platform"""

    async def run(self) -> str:
        return (await self.sh("uname")).strip().lower()

```

</details>

-------------------------------------------------

## fs.chmod

Changes the file mode of the specified path

### Arguments


- path *(str)* : The path to change the mode of
- mode *(str)* : The mode



<details>
<summary>Show source</summary>

```python
from pitcrew import task


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

-------------------------------------------------

## fs.chown

Changes the file mode of the specified path

### Arguments


- path *(str)* : The path to change the mode of
- owner *(str)* : The owner
- group *(str)* : The owner



<details>
<summary>Show source</summary>

```python
from pitcrew import task


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

-------------------------------------------------

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
from pitcrew import task


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

-------------------------------------------------

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
from pitcrew import task


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

-------------------------------------------------

## fs.is_directory

Checks if the path is a directory

### Arguments


- path *(str)* : The path to check


### Returns

*(bool)* Indicates if target path is a directory


<details>
<summary>Show source</summary>

```python
from pitcrew import task


@task.arg("path", desc="The path to check")
@task.returns("Indicates if target path is a directory")
class FsIsDirectory(task.BaseTask):
    """Checks if the path is a directory"""

    async def run(self) -> bool:
        code, _, _ = await self.sh_with_code(f"test -d {self.params.esc_path}")
        return code == 0

```

</details>

-------------------------------------------------

## fs.is_file

Checks if the path is a file

### Arguments


- path *(str)* : The path to check


### Returns

*(bool)* Indicates if target path is a file


<details>
<summary>Show source</summary>

```python
from pitcrew import task


@task.arg("path", desc="The path to check")
@task.returns("Indicates if target path is a file")
class FsIsFile(task.BaseTask):
    """Checks if the path is a file"""

    async def run(self) -> bool:
        code, _, _ = await self.sh_with_code(f"test -f {self.params.esc_path}")
        return code == 0

```

</details>

-------------------------------------------------

## fs.list

List the files in a directory.

### Arguments


- path *(str)* : The file to read


### Returns

*(list)* The bytes of the file


<details>
<summary>Show source</summary>

```python
from pitcrew import task


@task.arg("path", desc="The file to read", type=str)
@task.returns("The bytes of the file")
class FsList(task.BaseTask):
    """List the files in a directory."""

    async def run(self) -> list:
        out = await self.sh(f"ls -1 {self.params.esc_path}")
        return out.strip().split("\n")

```

</details>

-------------------------------------------------

## fs.read

Read value of path into bytes

### Arguments


- path *(str)* : The file to read


### Returns

*(bytes)* The bytes of the file


<details>
<summary>Show source</summary>

```python
from pitcrew import task


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

-------------------------------------------------

## fs.stat

Get stat info for path

### Arguments


- path *(str)* : The path of the file to stat


### Returns

*(Stat)* the stat object for the file


<details>
<summary>Show source</summary>

```python
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

```

</details>

-------------------------------------------------

## fs.touch

Touches a file

### Arguments


- path *(str)* : The path to change the mode of



<details>
<summary>Show source</summary>

```python
from pitcrew import task


@task.arg("path", desc="The path to change the mode of", type=str)
class FsTouch(task.BaseTask):
    """Touches a file"""

    async def run(self):
        return await self.sh(f"touch {self.params.esc_path}")

```

</details>

-------------------------------------------------

## fs.write

Write bytes to a file

### Arguments


- path *(str)* : The path of the file to write to
- content *(bytes)* : The contents to write



<details>
<summary>Show source</summary>

```python
import hashlib
from pitcrew import task


@task.arg("path", type=str, desc="The path of the file to write to")
@task.arg("content", type=bytes, desc="The contents to write")
class FsWrite(task.BaseTask):
    """Write bytes to a file"""

    async def verify(self):
        stat = await self.fs.stat(self.params.path)
        assert len(self.params.content) == stat.size
        expected_digest = hashlib.sha256(self.params.content).hexdigest()
        actual_digest = await self.fs.digests.sha256(self.params.path)
        assert actual_digest == expected_digest

    async def run(self):
        await self.sh(
            f"tee {self.params.esc_path} > /dev/null", stdin=self.params.content
        )


class FsWriteTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        with self.cd("/tmp"):
            await self.fs.write("some-file", b"some content")
            out = await self.sh("cat some-file")
            assert out == "some content"

```

</details>

-------------------------------------------------

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
from pitcrew import task


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
        assert (
            self.params.url in git_config.decode()
        ), f"url {self.params.url} couldn't be found in the .git/config"

    async def run(self):
        command = f"git clone {self.params.esc_url} {self.params.esc_destination}"
        await self.sh(command)

```

</details>

-------------------------------------------------

## homebrew.install

Read value of path into bytes

### Arguments


- name *(str)* : Package to install


### Returns

*(str)* the version installed


<details>
<summary>Show source</summary>

```python
from pitcrew import task


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

-------------------------------------------------

## install

Installs a package, optionally allowing the version number to specified.

This task defers exection to package-manager specific installation tasks, such as
homebrew or apt-get.
    

### Arguments


- name *(str)* : The name of the package to install


### Returns

*(str)* The version of the package installed


<details>
<summary>Show source</summary>

```python
from pitcrew import task


@task.arg("name", desc="The name of the package to install", type=str)
@task.returns("The version of the package installed")
class Install(task.BaseTask):
    """Installs a package, optionally allowing the version number to specified.

This task defers exection to package-manager specific installation tasks, such as
homebrew or apt-get.
    """

    async def run(self) -> str:
        installer_tasks = [self.homebrew.install, self.apt_get.install]
        for pkg in installer_tasks:
            task = pkg.task()
            if await task.available():
                return await task.invoke(name=self.params.name)
        raise Exception("cannot find a package manager to defer to")

```

</details>

-------------------------------------------------

## install.homebrew

Ensures xcode is installed





<details>
<summary>Show source</summary>

```python
from pitcrew import task


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

-------------------------------------------------

## install.xcode_cli

Ensures xcode is installed





<details>
<summary>Show source</summary>

```python
from pitcrew import task


class InstallXcodeCli(task.BaseTask):
    """Ensures xcode is installed"""

    async def verify(self):
        assert await self.fs.is_directory("/Library/Developer/CommandLineTools")

    async def run(self):
        await self.sh("xcode-select --install")
        await self.poll(self.verify)

```

</details>

-------------------------------------------------

## providers.docker

A provider for ssh contexts

### Arguments


- container_ids *(list)* : The container ids to use


### Returns

*(DockerProvider)* An async generator that gives ssh contexts


<details>
<summary>Show source</summary>

```python
from pitcrew import task


class DockerProvider:
    def __init__(self, context, container_ids):
        self.context = context
        self.container_ids = container_ids
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index == len(self.container_ids):
            raise StopAsyncIteration
        docker_ctx = self.context.docker_context(
            container_id=self.container_ids[self.index]
        )
        self.index += 1
        return docker_ctx

    def __str__(self):
        return f"DockerProvider(container_ids={self.container_ids})"


@task.returns("An async generator that gives ssh contexts")
@task.arg("container_ids", type=list, desc="The container ids to use")
class ProvidersDocker(task.BaseTask):
    """A provider for ssh contexts"""

    async def run(self) -> DockerProvider:
        return DockerProvider(self.context, self.params.container_ids)

```

</details>

-------------------------------------------------

## providers.local

A provider for a local context




### Returns

*(LocalProvider)* An async generator that gives a local context


<details>
<summary>Show source</summary>

```python
from pitcrew import task


class LocalProvider:
    def __init__(self, local_context):
        self.returned = False
        self.local_context = local_context

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.returned:
            self.returned = True
            return self.local_context
        else:
            raise StopAsyncIteration

    def __str__(self):
        return "LocalProvider"


@task.returns("An async generator that gives a local context")
class ProvidersLocal(task.BaseTask):
    """A provider for a local context"""

    async def run(self) -> LocalProvider:
        return LocalProvider(self.context.local_context)


class ProvidersLocalTest(task.TaskTest):
    @task.TaskTest.ubuntu
    async def test_ubuntu(self):
        async for p in await self.providers.local():
            assert p == self.context.local_context

```

</details>

-------------------------------------------------

## providers.ssh

A provider for ssh contexts

### Arguments


- user *(str)* : The user to use for the ssh contexts
- hosts *(list)* : The hosts to use for ssh contexts


### Returns

*(SSHProvider)* An async generator that gives ssh contexts


<details>
<summary>Show source</summary>

```python
from pitcrew import task
from netaddr.ip.nmap import iter_nmap_range


class SSHProvider:
    def __init__(self, context, hosts, user):
        self.context = context
        self.hosts = hosts
        self.flattened_hosts = list(
            map(lambda ip: str(ip), iter_nmap_range(*self.hosts))
        )
        self.user = user
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index == len(self.flattened_hosts):
            raise StopAsyncIteration
        ssh_ctx = self.context.ssh_context(
            host=self.flattened_hosts[self.index], user=self.user
        )
        self.index += 1
        return ssh_ctx

    def __str__(self):
        return f"SSHProvider(user={self.user} hosts={self.hosts})"


@task.returns("An async generator that gives ssh contexts")
@task.arg("user", type=str, desc="The user to use for the ssh contexts")
@task.arg("hosts", type=list, desc="The hosts to use for ssh contexts")
class ProvidersSsh(task.BaseTask):
    """A provider for ssh contexts"""

    async def run(self) -> SSHProvider:
        return SSHProvider(self.context, self.params.hosts, self.params.user)

```

</details>

-------------------------------------------------

