# j5 Ableton Control

Control and interact with Ableton Live via Python commands, shell, and/or REST Interface.

todo: video

### Install

Close Live, clone this repo, then from its directory (Mac OS X):
```bash
for live_dir in "$(find /Applications/Ableton* -name 'MIDI Remote Scripts')"; do
mkdir "$live_dir/j5 Control"
for f in *.py ; do ln -s "$(pwd)/$f" "$live_dir/j5 Control/$f" ; done ; done
```
Open `Live` -> `Preferences` -> `Link MIDI`, select `j5 Control` in any Control Surface column cell.

### Local Dev and Use

The default configuration enables HTTP REST interface, Python interaction (via REST),
but not the telnet shell. Default REST port is 8080.

After installing and enabling in Live,
open [./shell.html](./shell.html) to interact with Live, as an example.
(Can use `curl` or build any REST client interface as well)

The above install directions use symlinks, so local changes will propagate on restarts.
The Ableton Python REPL functionality via [./shell.html](./shell.html) is great for quick tests
without having to restart Live.

For better IDE integration, you can clone
[Ableton Live MIDI Remote Scripts source repo](https://github.com/gluon/AbletonLive11_MIDIRemoteScripts)
one directory above, as the Python module symlinks in this repo, `ableton` and `_Framework`, point there.

### Code Overview

| Python File                                                 | Description
|-------------------------------------------------------------|------------
| [\_\_init\_\_](./__init__.py)                               | Standard Python / Ableton Control Surface mechanism, short bootstrap
| [AbletonControlSurface](AbletonControlSurface.py)           | Bare-bones implementation of [Ableton Control Surface class](https://github.com/gluon/AbletonLive11_MIDIRemoteScripts/blob/main/_Framework/ControlSurface.py), bootstraps and delegating logic
| [AbletonControl](./AbletonControl.py)                       | Simple configurer for REST and Shell / Console impls
| [AbletonPythonRestResource](./AbletonPythonRestResource.py) | REST Resource implementing a collection of routes to control and introspect Ableton Live (e.g. `/play`, `/tempo/{bpm}`)
| [SimpleRestServer](./SimpleRestServer.py)                   | Basic, unoptimized impl of a non-blocking-Socket backed, `.tick()` based approach to HTTP / REST server, so that Ableton Live can run it. Leverages regular expression groups for quick and dirty route defining.
| [RemoteConsole](./RemoteConsole.py)                         | Leverage Python's code package's [InteractiveConsole](https://docs.python.org/3/library/code.html) to impl REPL functionality. (Supports telnet as wellnet). Hijacks `stdout` so results can be returned. 