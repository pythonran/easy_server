import os
import select
import tox
from utils import Configurable

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

    def __init__(self, *args, **kwargs):
        self.loop = None
        if hasattr(select, "epoll"):
            self.loop = select.epoll
        elif hasattr(select, "poll"):
            self.loop = select.poll
        else:
            self.loop = select.select

    def __call__(self, *args, **kwargs):

        pass

    def add_event(self, fd, event):
        event_loop = self.loop()
        event_loop.register(fd, event)
        pass

if __name__ == "__main__":
    loop = eventLoop()

    loop()
    pass