from __future__ import absolute_import, print_function, unicode_literals
import time, sys, socket, code, re, traceback, types
if sys.version.startswith('2'): from StringIO import StringIO
else: from io import StringIO

u"""
todo: could use some clean up, plus doesn't work with multiple connects,
IO / stdout redirection needs improving
"""

DEF_PATTERN = re.compile(r'\s*(def\s+([^(]+)\s*\(\s*self\s*[),])')

class RemoteConsole:
    u""" Allow non-blocking Python REPL """
    def __init__(self, ctx=None, port=11012, bind_address='0.0.0.0', welcome="Remote Python REPL connected",
                 listen=True, log=None, connect_interval_secs=3.0):
        self.port = port
        self.bind_address = bind_address
        self.connect_interval_secs = connect_interval_secs
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)
        self.welcome = welcome
        self.listening = False
        self.log = types.MethodType(log or self.log, self)
        if listen:
            self.listen()
        self.log('Initializing RemoteConsole on port', port)
        self.context = dict(globals())
        self.context['console'] = self
        if ctx:
            self.context.update(ctx)
        if 'self' not in self.context:
            self.context['self'] = self
        self.should_listen = listen
        self.last_connect_check = 0.0
        self.interpreters = []
        self.default_interpreter = None
        self.clients = []

    def try_connect(self):
        try:
            conn, addr = self.server_socket.accept()
        except socket.error as socket_error:
            if socket_error.errno != socket.EAGAIN:
                self.log('Error (not expected try again) during connection accept, raising:', socket_error)
                raise socket_error
        else:
            self.send(conn, self.welcome + "\n>>> ")
            self.clients.append(conn)
            self.interpreters.append(self.new_interpreter())

    def listen(self):
        if self.listening:
            self.log('Socket already listening, skipping')
        try:
            self.server_socket.bind((self.bind_address, self.port))
            self.server_socket.listen(1)
            self.listening = True
            self.log('Shell socket listening on port {}'.format(self.port))
        except BaseException as e:
            self.log("\n\n\n*** Shell socket start failed, will try again:", e, "***\n\n\n")
        return self.listening

    def tick(self):
        if not self.listening and not self.listen():
            return
        if time.time() - self.last_connect_check > self.connect_interval_secs:
            self.try_connect()
            self.last_connect_check = time.time()
        self.try_read_commands()

    def try_read_commands(self):
        for index, client in enumerate(self.clients):
            cmds = ""
            start_time = time.time()
            while time.time() - start_time < 0.090:
                try:
                    cmds += client.recv(4096).decode("ascii")
                except socket.error as socket_error:
                    if socket_error.errno != socket.EAGAIN:
                        self.log('Error during command read, raising non-try again socket error:', socket_error)
                        raise socket_error
                    break
            if cmds:
                self.execute_commands(index, client, cmds)

    def execute_commands(self, index, client, cmds):
        self.log('Read command:\n', cmds)
        if cmds in ['quit\n', 'exit\n']:
            self.try_socket_close('client {}'.format(index), client)
            self.clients.remove(client)
        elif cmds == 'shutdown\n':
            self.shutdown()
        else:
            return self.run_and_prompt(index, cmds)

    def run_and_prompt(self, index, source):
        incomplete, output, buffer = self.run_cmd(self.interpreters[index], source)
        if incomplete:
            self.send(self.clients[index], "... ")
        else:
            self.send(self.clients[index], output)
            self.send(self.clients[index], ">>> ")
        return incomplete, output, buffer
    
    def send(self, conn, msg):
        conn.sendall(msg.encode("ascii"))

    """Temporarily hack replace std(out|err), since exec() is used by interp"""
    def run_cmd_single(self, interpreter, cmd):
        self.log("Executing:\n", cmd)
        stdout = sys.stdout
        stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        buffer = list(interpreter.buffer) + [cmd]
        incomplete = interpreter.push(cmd)
        output = sys.stdout.getvalue()
        output += sys.stderr.getvalue()
        sys.stdout = stdout
        sys.stderr = stderr
        self.log('Result:', incomplete, '\n', output)
        return incomplete, output, buffer

    def run_cmd(self, interpreter, cmd):
        binds = []
        if DEF_PATTERN.search(cmd):
            cmd = DEF_PATTERN.sub(r"\n\n\1", cmd)
            for method_match in DEF_PATTERN.findall(cmd):
                method = method_match[1]
                binds.append('self.{} = rc_types.MethodType({}, self)\n\n'.format(method, method))
            cmd += '\n\n'
        results = list(map(lambda c: self.run_cmd_single(interpreter, c), [cmd] + binds))
        return results[-1]
    
    def run_cmd_with_default_interpreter(self, cmd):
        if not self.default_interpreter:
            self.default_interpreter = self.new_interpreter()
        return self.run_cmd(self.default_interpreter, cmd)

    def new_interpreter(self):
        interpreter = code.InteractiveConsole(locals=self.context)
        interpreter.push("\nimport types as rc_types\n\n")
        return interpreter

    def log(self, *args):
        print(*args)

    def shutdown(self):
        self.log('Shutting down')
        for index, client in enumerate(self.clients):
            self.try_socket_close("client " + str(index), client)
        self.try_socket_close("server", self.server_socket)

    def try_socket_close(self, name, socket_instance):
        def sclose(action, callback):
            try:
                self.log("Executing", action)
                callback()
            except BaseException as e:
                self.log("Error during", action, e)
        sclose(name + " socket shutdown", lambda: socket_instance.shutdown(socket.SHUT_RDWR))
        sclose(name + " socket close", lambda: socket_instance.close())


if __name__ == "__main__":
    import signal, traceback, os
    console = RemoteConsole(port=int(os.environ.get('RC_PORT') or '10141'))
    console.running = True

    def signal_handler(sig, frame):
        console.log("Shutdown hook")
        console.running = False
        console.shutdown()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    while console.running:
        try:
            console.tick()
        except BaseException as e:
            console.log("Error ticking:", e)
            traceback.print_exc()
        time.sleep(0.100)


