import asyncssh
from pitcrew import task
from netaddr.ip.nmap import iter_nmap_range


class SSHProvider:
    def __init__(self, context, hosts, user, tunnels=[], **connection_args):
        self.context = context
        self.hosts = hosts
        self.tunnels = tunnels
        self.connection_args = connection_args
        self.flattened_hosts = self.__generate_flattened_hosts()
        self.user = user
        self.index = 0
        self.tunnel_contexts = []

    async def __aenter__(self):
        last_tunnel = None
        for tunnel in self.tunnels:
            context = self.context.ssh_context(tunnel=last_tunnel, **tunnel)
            self.tunnel_contexts.append(context)
            await context.__aenter__()
            last_tunnel = context.connection

    async def __aexit__(self, exc_type, exc_value, traceback):
        for context in reversed(self.tunnel_contexts):
            try:
                await context.__aexit__()
            except:
                pass
        if exc_type:
            raise exc_value.with_traceback(traceback)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index == len(self.flattened_hosts):
            raise StopAsyncIteration

        tunnel = self.tunnel_contexts[-1].connection if self.tunnel_contexts else None
        ssh_ctx = self.context.ssh_context(
            host=self.flattened_hosts[self.index], user=self.user, tunnel=tunnel
        )
        self.index += 1
        return ssh_ctx

    def __str__(self):
        return f"SSHProvider(user={self.user} hosts={self.hosts})"

    def __generate_flattened_hosts(self):
        hosts = []
        for host in self.hosts:
            try:
                hosts.append(map(lambda ip: str(ip), list(iter_nmap_range(host))))
            except:
                hosts.append(host)
        return hosts


@task.returns("An async generator that gives ssh contexts")
@task.arg("hosts", type=list, desc="The hosts to use for ssh contexts")
@task.arg(
    "tunnels", type=list, desc="The set of tunnels to connect through", default=[]
)
@task.opt("user", type=str, desc="The user to use for the ssh contexts")
@task.opt(
    "agent_forwarding",
    type=bool,
    default=False,
    desc="Specify if forwarding is enabled",
)
@task.opt("agent_path", type=str, desc="Specify if forwarding is enabled")
class ProvidersSsh(task.BaseTask):
    """A provider for ssh contexts"""

    async def run(self) -> SSHProvider:
        extra_args = {}
        if self.params.agent_path:
            extra_args["agent_path"] = self.params.agent_path
        return SSHProvider(
            self.context,
            self.params.hosts,
            self.params.user,
            tunnels=self.params.tunnels,
            agent_forwarding=self.params.agent_forwarding,
            **extra_args,
        )
