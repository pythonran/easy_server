import os
import select
import tox
from utils import Configurable
from loop import _kqueue, _select

class eventLoop(object):
    EPOLLERR = 8
    EPOLLET = 2147483648
    EPOLLHUP = 16
    EPOLLIN = 1
    EPOLLMSG = 1024
    EPOLLONESHOT = 1073741824
    EPOLLOUT = 4
    EPOLLPRI = 2
    EPOLLRDBAND = 128
    EPOLLRDNORM = 64
    EPOLLWRBAND = 512
    EPOLLWRNORM = 256

    PIPE_BUF = 4096

    POLLERR = 8
    POLLHUP = 16
    POLLIN = 1
    POLLMSG = 1024
    POLLNVAL = 32
    POLLOUT = 4
    POLLPRI = 2
    POLLRDBAND = 128
    POLLRDNORM = 64
    POLLWRBAND = 512
    POLLWRNORM = 256

    def __init__(self, sock=None):
        self.loop = None
        if hasattr(select, "epoll"):
            print "now in epoll"
            self.loop = select.epoll()
        elif hasattr(select, "kqueue"):
            print "now in kqueue"
            self.loop = _kqueue._KQueue()
        else:
            print "now in select"
            self.loop = _select._Select()
        if sock:
            self.add_event(sock.fileno(), self.EPOLLIN)

    def __call__(self, *args, **kwargs):

        pass

    def add_event(self, fd, event):
        self.loop.register(fd, event)

    def update_event(self, fd, event):
        self.loop.modify(fd, event)

    def remove_event(self, fd):
        self.loop.unregister(fd)

if __name__ == "__main__":
    loop = eventLoop()

    loop()
    pass