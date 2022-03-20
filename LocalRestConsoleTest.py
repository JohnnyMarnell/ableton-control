import signal, traceback, os, time, sys
from RemoteConsole import RemoteConsole
from SimpleRestServer import SimpleRestServer

console = RemoteConsole(port=int(os.environ.get('RC_PORT') or '10140'))
console.running = True
rest = SimpleRestServer()
num_runs = 0


def run_cmd(cmd):
    global num_runs
    num_runs += 1
    incomplete, output, buffer = console.run_cmd_with_default_interpreter(cmd)
    return {
        'complete': not incomplete,
        'output': str(output).strip(),
        'buffer': buffer
    }


rest.add_route('POST', '/run', lambda req: run_cmd(req['body']['command']))
rest.add_route('GET', '/state', lambda req: {'runs': num_runs})


def signal_handler(sig, frame):
    console.log("Shutdown hook")
    console.running = False
    console.shutdown()
    rest.shutdown()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

while console.running:
    try:
        console.tick()
        rest.tick()
    except BaseException as e:
        console.log("Error ticking:", e)
        traceback.print_exc()
    time.sleep(0.100)



