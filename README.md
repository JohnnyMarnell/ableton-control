# ableton-resticle

Simple REST control of Ableton Live Proof-of-Concept.

### Demo

[![Quick vid](https://img.youtube.com/vi/R38JhEbVTUc/maxresdefault.jpg)](https://youtu.be/R38JhEbVTUc)

### Install

**Live 11 and up** read user scripts out of the User Library, so nothing goes into the
app bundle and an upgrade doesn't wipe it. Close Live, clone this repo, then from its dir
(macOS):

```bash
dest=~/Music/Ableton/"User Library"/"Remote Scripts"/Resticle
mkdir -p "$dest"
for f in *.py ; do ln -s "$(pwd)/$f" "$dest/$f" ; done
```

<details><summary>Live 10 and older (into the app bundle)</summary>

```bash
live_dir="$(find /Applications/Ableton* -name 'MIDI Remote Scripts')"
mkdir "$live_dir/Resticle"
for f in *.py ; do ln -s "$(pwd)/$f" "$live_dir/Resticle/$f" ; done
```
</details>

Open Live -> Settings -> **Tempo & MIDI** (Link, MIDI before Live 12), select **Resticle**
in any Control Surface column cell. It has to be re-selected after a reinstall, and Live
only rescans the scripts folder at startup.

Serves on **127.0.0.1:8080** — loopback only, since this is unauthenticated control of
whatever Live has open.

### Testing

`python3 test_resticle.py` exercises the server against a fake Live song object: no Live,
no Ableton imports, so it runs anywhere. Worth running before you restart Live, because a
remote script that throws is a dead Control Surface whose only trace is Live's log.

### API

```bash
$ curl -XPOST localhost:8080/play
# {"ok": true}
$ curl -XPOST localhost:8080/stop
# {"ok": true}
$ curl -XPOST localhost:8080/continue
# {"ok": true}
$ curl -XGET  localhost:8080/tempo
# {"tempo": 120.0}
$ curl -XPOST localhost:8080/tempo/150
# {"tempo": 150.0}
$ curl -XPOST localhost:8080/metronome/1
# {"metronome": true}
$ curl -XGET  localhost:8080/song
# {"tempo": 150.0, "is_playing": true, "current_song_time": 12.5,
#  "signature_numerator": 4, "signature_denominator": 4, "metronome": true}
```

`/song` is everything in one read, so a caller asserting what Live is doing polls one
route instead of racing several.