class AbletonPythonResticleResource:
    """ Implementing a few routes as examples """
    def __init__(self, application, song):
        self.song = song
        self.application = application

    def add_routes(self, server):
        ok = {'ok': True}
        server.add_route('GET', '/tempo', lambda p, h: {'tempo': self.song.tempo})

        server.add_route('POST', '/tempo/{bpm}', lambda p, h: self.set_tempo(float(p['bpm'])))

        server.add_route('POST', '/play', lambda p, h: self.song.start_playing() or ok)
        server.add_route('POST', '/stop', lambda p, h: self.song.stop_playing() or ok)
        server.add_route('POST', '/continue', lambda p, h: self.song.continue_playing() or ok)

        # Everything a caller needs to assert what Live is actually doing, in one read —
        # so a test can poll one route instead of racing several
        server.add_route('GET', '/song', lambda p, h: self.song_state())
        server.add_route('POST', '/metronome/{on}', lambda p, h: self.set_metronome(p['on']))

    def set_tempo(self, tempo):
        self.song.tempo = tempo
        return {'tempo': tempo}

    def song_state(self):
        return {
            'tempo': self.song.tempo,
            'is_playing': self.song.is_playing,
            'current_song_time': self.song.current_song_time,
            'signature_numerator': self.song.signature_numerator,
            'signature_denominator': self.song.signature_denominator,
            'metronome': self.song.metronome,
        }

    def set_metronome(self, on):
        self.song.metronome = on not in ('0', 'off', 'false')
        return {'metronome': self.song.metronome}

    # etc, etc
