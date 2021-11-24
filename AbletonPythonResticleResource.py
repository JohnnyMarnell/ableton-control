class AbletonPythonResticleResource:
    """ Implementing a few routes as examples """
    def __init__(self, application, song):
        self.song = song
        self.application = application

    def add_routes(self, server):
        ok = {'ok': True}
        server.add_route('GET', '/tempo', lambda p, h: {'tempo': self.song.tempo}, 'GET')

        server.add_route('POST', '/tempo/{bpm}', lambda p, h: self.set_tempo(float(p['bpm'])))

        server.add_route('POST', '/play', lambda p, h: self.song.start_playing() or ok)
        server.add_route('POST', '/stop', lambda p, h: self.song.stop_playing() or ok)

    def set_tempo(self, tempo):
        self.song.tempo = tempo
        return {'tempo': tempo}

    # etc, etc
