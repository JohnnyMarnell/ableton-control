from __future__ import absolute_import, print_function, unicode_literals
import Live, sys, time
from .SimpleRestServer import SimpleRestServer
from .AbletonPythonRestResource import AbletonPythonRestResource
from .RemoteConsole import RemoteConsole

class AbletonControl:
    """ Simple bootstrapper / delegator to REST, interpreter, and telnet shell features """
    def __init__(self, c_instance, control_surface, ctx, rest=True, rest_commands=True, shell=False,
                 rest_port=8080, shell_port=11012, log=None):
        self.rest = rest or rest_commands
        self.shell = shell
        self.console = None
        if shell or rest_commands:
            context = dict()
            context.update(globals())
            context.update({
                'self': control_surface,
                'c_instance': c_instance,
                'Live': Live
            })
            context.update(ctx)
            self.console = RemoteConsole(ctx=context, listen=shell, port=shell_port, log=log)
        
        self.rest_server = SimpleRestServer(listen=self.rest, port=rest_port, log=log)
        self.resource = AbletonPythonRestResource(c_instance)
        self.resource.add_routes(self.rest_server)
        if rest_commands:
            self.resource.add_console_route(self.rest_server, self.console)

    def tick(self):
        if self.rest:
            self.rest_server.tick()
        if self.shell:
            self.console.tick()

    def shutdown(self):
        if self.rest:
            self.rest_server.shutdown()
        if self.shell:
            self.console.shutdown()
