import contextlib
import functools
import threading
class Context(object):
    def __init__(self, func):
        self.ret = func()
        pass

    def __call__(self, func, *args, **kwargs):
        pass

    def __enter__(self):
        return self.ret.next()

    def __exit__(self, type, value, traceback):
        print "traceback:", traceback
        return False

@Context
def process():
    try:
        return 1
    except Exception as e:
        print e

def callback():
    print "a delay task running"
    raise Exception

def run():
    print "main process running"
    thread = threading.Thread(target=callback)
    thread.daemon = False
    thread.start()
    print "main process over"

try:
    run()
    print "run is health"
except Exception as exc:
    print "run error:", exc