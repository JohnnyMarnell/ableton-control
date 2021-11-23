
""" Just a few routes as examples """
class AbletonPythonResticleResource:
    def __init__(self, application, song):
        self.song = song
        self.application = application

    def add_routes(self, server):
        ok = {'ok': True}
        server.add_route('/tempo', lambda p, h: {'tempo': self.song.tempo}, 'GET')

        server.add_route('/tempo/{bpm}', lambda p, h: self.set_tempo(float(p['bpm'])), 'POST')

        server.add_route('/play', lambda p, h: self.song.start_playing() or ok, 'POST')
        server.add_route('/stop', lambda p, h: self.song.stop_playing() or ok, 'POST')

    def set_tempo(self, tempo):
        self.song.tempo = tempo
        return {'tempo': tempo}


    # etc, etc