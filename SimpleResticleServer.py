from __future__ import absolute_import, print_function, unicode_literals
import sys, socket, collections, re, json, time, errno

Route = collections.namedtuple('Route', 'method pattern handler')

# accept() on a non-blocking socket raises one of these when there is nobody waiting
WOULD_BLOCK = (errno.EAGAIN, errno.EWOULDBLOCK)
# a request Live's tick loop should never stall on; the client is on this machine
CLIENT_TIMEOUT_S = 0.5


class SimpleResticleServer:
    """
     Simple REST server implementation, uses non-blocking socket + tick loop approach, so
     it works with Ableton's embedded Python via Remote Scripts
    """
    def __init__(self, port=8080, bind_address='127.0.0.1'):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)
        self.server_socket.bind((bind_address, port))
        self.server_socket.listen(8)
        self.routes = []
        print('Listening on %s port %s ...' % (bind_address, port))

    """ Leverage RegEx named groups for quick and dirty REST path parameters """
    def add_route(self, method, path, handler):
        # Anchored: re.match is a prefix match, so an unanchored '/tempo' would answer
        # for '/tempo/150' and whichever route was added first would win
        pattern = re.compile(r'/\{([^}]+)\}').sub(r'/(?P<\1>[^/]+)', path) + '$'
        self.routes.append(Route(method, re.compile(pattern), handler))
        print('Added route:', method, path)

    """ Parse HTTP request (path, headers, etc), find route and dispatch """
    def serve_request(self, request):
        # Nothing a caller sends may reach Live's tick loop as an exception: a dead
        # control surface is a Live restart, and the message would only be in the log
        try:
            lines = request.split('\n')
            method, path, scheme = lines[0].split(' ')
            path = path.split('?')[0]
            headers = {}
            for header in lines[1:]:
                if header.strip() == "":
                    break
                colon = header.index(":")
                headers[header[0:colon].strip().lower()] = header[colon + 1:].strip()
            # todo: if json header, parse body
            # todo: query string params
            for route in self.routes:
                if route.method == method:
                    match = route.pattern.match(path)
                    if match:
                        body = route.handler(match.groupdict(), headers)
                        return 'HTTP/1.0 200 OK\nContent-Type: application/json\n\n' + json.dumps(body)
            return 'HTTP/1.0 404 NOT FOUND\nContent-Type: application/json\n\n' + json.dumps(
                {'error': 'no route', 'method': method, 'path': path})
        except Exception as e:
            print('Server error', repr(e))
            return 'HTTP/1.0 500 INTERNAL SERVER ERROR\nContent-Type: application/json\n\n' + json.dumps(
                {'error': repr(e)})

    """ Handle any pending requests / connections """
    def tick(self):
        while True:
            try:
                client, client_address = self.server_socket.accept()
            except OSError as e:
                # Python 3 has no socket.errno, and a bare accept() with nobody
                # waiting raises BlockingIOError — an OSError, not socket.error
                if e.errno in WOULD_BLOCK:
                    break
                raise
            # The listening socket is non-blocking and the accepted one inherits that on
            # macOS, so recv() can beat the request in. A short timeout reads it without
            # ever parking Live's tick loop on a client that went away mid-send.
            try:
                client.settimeout(CLIENT_TIMEOUT_S)
                request = client.recv(2048).decode()
                client.sendall(self.serve_request(request).encode())
            except (OSError, UnicodeDecodeError) as e:
                print('Server dropped a request:', e)
            finally:
                client.close()

    def shutdown(self):
        self.server_socket.close()


if __name__ == "__main__":
    server = SimpleResticleServer()
    import signal

    def signal_handler(sig, frame):
        server.shutdown()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    server.add_route('GET', '/echo/{a}/{b}', lambda path_params, headers: {
        'path_params': path_params, 'headers': headers})
    while True:
        server.tick()
        time.sleep(0.200)

