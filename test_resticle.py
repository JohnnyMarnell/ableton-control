# /// script
# requires-python = ">=3.9"
# ///
"""
Resticle's server against the Python Live 12 actually embeds — no Live, no Ableton
imports. Run it before installing: `uv run test_resticle.py` (or python3 test_resticle.py).

What it is really checking is that the non-blocking accept loop survives Python 3,
where `socket.errno` is gone and a bare accept() raises BlockingIOError.
"""
import json
import threading
import time
import urllib.error
import urllib.request

from AbletonPythonResticleResource import AbletonPythonResticleResource
from SimpleResticleServer import SimpleResticleServer

PORT = 8099
BASE = 'http://127.0.0.1:%d' % PORT


class FakeSong:
    """Only the Live LOM members the resource touches."""
    def __init__(self):
        self.tempo = 120.0
        self.is_playing = False
        self.current_song_time = 0.0
        self.signature_numerator = 4
        self.signature_denominator = 4
        self.metronome = False

    def start_playing(self):
        self.is_playing = True

    def stop_playing(self):
        self.is_playing = False

    def continue_playing(self):
        self.is_playing = True


def request(method, path, timeout=2.0):
    req = urllib.request.Request(BASE + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def main():
    song = FakeSong()
    server = SimpleResticleServer(port=PORT)
    AbletonPythonResticleResource(application=None, song=song).add_routes(server)

    # Live calls tick() from update_display every 100 ms; same shape here
    stop = threading.Event()

    def pump():
        while not stop.is_set():
            server.tick()
            time.sleep(0.02)

    thread = threading.Thread(target=pump, daemon=True)
    thread.start()

    failures = []

    def check(what, got, want):
        if got != want:
            failures.append('%s: got %r, wanted %r' % (what, got, want))
        print(('  ok  ' if got == want else '  FAIL') + '  %s -> %r' % (what, got))

    # An idle tick loop must not throw: this is the Python 3 bug, and it only shows
    # up as the control surface dying after Live's first update_display
    for _ in range(5):
        server.tick()

    check('GET /tempo', request('GET', '/tempo'), (200, {'tempo': 120.0}))
    check('POST /tempo/140', request('POST', '/tempo/140'), (200, {'tempo': 140.0}))
    check('tempo reached the song', song.tempo, 140.0)

    check('POST /play', request('POST', '/play'), (200, {'ok': True}))
    check('song is playing', song.is_playing, True)
    check('POST /stop', request('POST', '/stop'), (200, {'ok': True}))
    check('song stopped', song.is_playing, False)
    check('POST /continue', request('POST', '/continue'), (200, {'ok': True}))
    check('song continued', song.is_playing, True)

    status, body = request('GET', '/song')
    check('GET /song status', status, 200)
    check('GET /song tempo', body.get('tempo'), 140.0)
    check('GET /song is_playing', body.get('is_playing'), True)

    check('POST /metronome/1', request('POST', '/metronome/1'), (200, {'metronome': True}))
    check('POST /metronome/off', request('POST', '/metronome/off'), (200, {'metronome': False}))

    # Anchored routes: '/tempo' must not answer for '/tempo/150' or '/tempotrap'
    check('GET /tempotrap is 404', request('GET', '/tempotrap')[0], 404)
    check('GET /nope is 404', request('GET', '/nope')[0], 404)

    # A handler that raises is a 500, not a dead control surface
    server.add_route('GET', '/boom', lambda p, h: (_ for _ in ()).throw(RuntimeError('boom')))
    check('GET /boom is 500', request('GET', '/boom')[0], 500)
    check('still serving after a raise', request('GET', '/tempo')[0], 200)

    # Many requests back to back, the way a test driving Live would
    codes = {request('GET', '/song')[0] for _ in range(25)}
    check('25 requests all 200', codes, {200})

    stop.set()
    thread.join(timeout=2)
    server.shutdown()

    print()
    if failures:
        print('FAILED (%d):' % len(failures))
        for f in failures:
            print(' -', f)
        raise SystemExit(1)
    print('all good')


if __name__ == '__main__':
    main()
