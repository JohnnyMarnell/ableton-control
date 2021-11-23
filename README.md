# ableton-resticle

Simple REST control of Ableton Live Proof-of-Concept.

### Demo

[![Quick vid](https://img.youtube.com/vi/R38JhEbVTUc/maxresdefault.jpg)](https://youtu.be/R38JhEbVTUc)

### Install

Close Live, clone this repo, then from its dir (Mac OS X):
```bash
live_dir="$(find /Applications/Ableton* -name 'MIDI Remote Scripts')"
mkdir "$live_dir/Resticle"
for f in *.py ; do ln -s "$(pwd)/$f" "$live_dir/Resticle/$f" ; done
```

Open Live -> Preferences -> Link MIDI, select Resticle in any Control Surface column cell.

### API Sample

```bash
$ curl -XPOST localhost:8080/play
# {"ok": true}
$ curl -XPOST localhost:8080/stop
# {"ok": true}
$ curl -XGET  localhost:8080/tempo
# {"tempo": 120.0}
$ curl -XPOST localhost:8080/play
# {"ok": true}
$ curl -XPOST localhost:8080/tempo/150
# {"tempo": 150.0}
$ curl -XPOST localhost:8080/stop
# {"ok": true}
```