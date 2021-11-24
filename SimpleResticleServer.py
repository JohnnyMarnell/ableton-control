from __future__ import absolute_import, print_function, unicode_literals
import sys, socket, collections, re, json, time

Route = collections.namedtuple('Route', 'method pattern handler')


class SimpleResticleServer:
    """
     Simple REST server implementation, uses non-blocking socket + tick loop approach, so
     it works with Ableton's embedded Python via Remote Scripts
    """
    def __init__(self, port=8080, bind_address='0.0.0.0'):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)
        self.server_socket.bind((bind_address, port))
        self.server_socket.listen(1)
        self.routes = []
        print('Listening on port %s ...' % port)

    """ Leverage RegEx named groups for quick and dirty REST path parameters """
    def add_route(self, method, path, handler):
        pattern = re.compile(r'/\{([^}]+)\}').sub(r'/(?P<\1>[^/]+)', path)
        self.routes.append(Route(method, re.compile(pattern), handler))
        print('Added route:', method, path)

    """ Parse HTTP request (path, headers, etc), find route and dispatch """
    def serve_request(self, request):
        lines = request.split('\n')
        method, path, scheme = lines[0].split(' ')
        headers = {}
        for header in lines[1:]:
            if header.strip() == "":
                break
            colon = header.index(":")
            headers[header[0:colon].strip().lower()] = header[colon + 1:].strip()
        # todo: if json header, parse body
        # todo: query string params
        try:
            for route in self.routes:
                if route.method == method:
                    match = route.pattern.match(path)
                    if match:
                        body = route.handler(match.groupdict(), headers)
                        return 'HTTP/1.0 200 OK\nContent-Type: application/json\n\n' + json.dumps(body)
            return 'HTTP/1.0 404 NOT FOUND\n\nNot Found'
        except ValueError as e:
            print('Server error', e)
            return 'HTTP/1.0 500 INTERNAL SERVER ERROR\n\nInternal Server Error'

    """ Handle any pending requests / connections """
    def tick(self):
        while True:
            try:
                client, client_address = self.server_socket.accept()
                request = client.recv(2048).decode()
            except socket.error as e:
                if e.errno == socket.errno.EAGAIN:
                    break
                else:
                    raise e
            response = self.serve_request(request)
            client.sendall(response.encode())
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

