from __future__ import absolute_import, print_function, unicode_literals
import sys, socket, collections, re, json, time, types

Route = collections.namedtuple('Route', 'method pattern handler')


class SimpleRestServer:
    """
     Simple REST server implementation, uses non-blocking socket + tick loop approach, so
     it works with Ableton's embedded Python via Remote Scripts
    """
    def __init__(self, port=8080, bind_address='0.0.0.0', listen=True, cors_all=True, log=None):
        self.port = port
        self.bind_address = bind_address
        self.listening = False
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)
        self.routes = []
        self.cors_all = cors_all
        if log:
            self.log = types.MethodType(log, self)
        if listen:
            self.listen()

    """ Leverage RegEx named groups for quick and dirty REST path parameters """
    def add_route(self, method, path, handler):
        pattern = re.compile(r'/\{([^}]+)\}').sub(r'/(?P<\1>[^/]+)', path)
        self.routes.append(Route(method, re.compile(pattern), handler))
        self.log('Added route:', method, path)

    """ Parse HTTP request (path, headers, etc), find route and dispatch """
    def serve_request(self, request):
        lines = request.split('\n')
        method, path, scheme = lines[0].split(' ')
        if method == 'OPTIONS' and self.cors_all:
            return 'HTTP/1.0 204 OK\n' + \
                   'Access-Control-Allow-Origin: *\n' + \
                   'Access-Control-Allow-Methods: *\n' + \
                   'Access-Control-Allow-Headers: *\n' + \
                   'Access-Control-Max-Age: 86400\n\n'
        headers = {}
        index = 1
        for header in lines[1:]:
            if header.strip() == "":
                break
            index += 1
            colon = header.index(":")
            headers[header[0:colon].strip().lower()] = header[colon + 1:].strip()
        body = '\n'.join(lines[index:])
        try:
            body = json.loads(body)
        except:
            pass
        # todo: if json header, parse body
        # todo: query string params
        try:
            for route in self.routes:
                if route.method == method:
                    match = route.pattern.match(path)
                    if match:
                        response_body = route.handler({
                            'path': match.groupdict(),
                            'headers': headers,
                            'body': body
                        })
                        res = 'HTTP/1.0 200 OK\n'
                        if self.cors_all:
                            res += 'Access-Control-Allow-Origin: *\n'
                        return res + 'Content-Type: application/json\n\n' + json.dumps(response_body)
            return 'HTTP/1.0 404 NOT FOUND\n\nNot Found'
        except ValueError as e:
            print('Server error', e)
            return 'HTTP/1.0 500 INTERNAL SERVER ERROR\n\nInternal Server Error'

    """ Handle any pending requests / connections """
    def tick(self):
        if not self.listening and not self.listen():
            return
        while True:
            try:
                client, client_address = self.server_socket.accept()
                request = client.recv(8192).decode()
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
    
    def listen(self):
        try:
            self.server_socket.bind((self.bind_address, self.port))
            self.server_socket.listen(1)
            self.listening = True
            self.log('HTTP server listening on port {}'.format(self.port))
        except BaseException as e:
            self.log("\n\n\n*** HTTP server start failed, will try again:", e, "***\n\n\n")
        return self.listening
    
    def log(self, *args):
        print(*args)


if __name__ == "__main__":
    server = SimpleRestServer()
    import signal

    def signal_handler(sig, frame):
        server.shutdown()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    server.add_route('GET', '/echo/{a}/{b}', lambda res: res)
    while True:
        server.tick()
        time.sleep(0.200)

