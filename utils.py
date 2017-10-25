import os
import threading
from functools import wraps

class Configurable(object):

    def __new__(cls, *args, **kwargs):
        pass

    def config_base(self):
        pass

    def config_default(self):
        pass
    pass


def async(fun):
    @wraps(fun)
    def inner(*args, **kwargs):
        thread = threading.Thread(target=fun, args=args, kwargs=kwargs)
        print args
        thread.daemon = kwargs["daemon"]
        thread.start()
        return str(thread.ident) + "_" + thread.name
    return inner