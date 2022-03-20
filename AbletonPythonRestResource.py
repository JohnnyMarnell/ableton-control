""" Implementing a few routes as examples """
import Live, time, collections

Event = collections.namedtuple('Event', 'type val desc time data')
EMPTY_EVENT = Event(type='any', val={}, desc='Empty', time=0.0, data={})

class AbletonPythonRestResource:
    def __init__(self, c_instance):
        self.c_instance = c_instance
        self.song = c_instance.song()
        self.application = Live.Application.get_application()
        self.events = []

    def add_routes(self, server):
        ok = {'ok': True}
        server.add_route('GET', '/tempo', lambda req: {'tempo': self.song.tempo})
        server.add_route('GET', '/events', lambda req: self.get_events())
        server.add_route('GET', '/state', lambda req: self.get_state())

        server.add_route('POST', '/tempo/{bpm}', lambda req: self.set_tempo(float(req['path']['bpm'])))
        server.add_route('POST', '/event', lambda req: self.add_event(**req['body']))
        server.add_route('POST', '/play', lambda req: self.song.start_playing() or ok)
        server.add_route('POST', '/stop', lambda req: self.song.stop_playing() or ok)
    
    def add_console_route(self, server, console):
        def run_cmd(cmd):
            incomplete, output, buffer = console.run_cmd_with_default_interpreter(cmd)
            return {
                'complete': not incomplete,
                'output': str(output).strip(),
                'buffer': buffer
            }
        server.add_route('POST', '/run', lambda req: run_cmd(req['body']['command']))

    def set_tempo(self, tempo):
        self.song.tempo = tempo
        return {'tempo': tempo}

    def get_events(self):
        return {'time': time.time(), 'events': [e._asdict() for e in self.events]}

    def get_state(self):
        state = {
            'overdub': self.song.overdub,
            'session_record': self.song.session_record,
            'playing': self.song.is_playing,
            'current_song_time': self.song.current_song_time,
            'tempo': self.song.tempo,
            'time_signature_numerator': self.song.signature_numerator,
            'tracks': [{
                'name': t.name,
                'midi': t.has_midi_input,
                'main_device': next((d.name for d in t.devices if d.__class__.__name__ in
                                     ['RackDevice', 'PluginDevice']), False)
            } for t in self.song.tracks]
        }
        clip = self.song.tracks[0].clip_slots[0].has_clip and self.song.tracks[0].clip_slots[0].clip
        if clip:
            state['clip'] = {
                'length': clip.loop_end - clip.loop_start,
                'playing_position': clip.playing_position,
                'position': clip.position,
                'num_notes': len(clip.get_notes(0.0, 0, 99999999999.0, 128))
            }
        state.update(self.get_events())
        return state

    def add_event(self, **kwargs):
        event = EMPTY_EVENT._replace(time=time.time(), **kwargs)
        self.events = [e for e in self.events if e.type != event.type and e.time >= event.time - 10.0]
        self.events.append(event)

    # etc, etc
