import select
# from eventloop import eventLoop

class _Select(object):
    """A simple, select()-based eventLoop implementation for non-Linux systems"""
    def __init__(self):
        self.read_fds = set()
        self.write_fds = set()
        self.error_fds = set()
        self.fd_sets = (self.read_fds, self.write_fds, self.error_fds)

    def close(self):
        pass

    def register(self, fd, events):
        if fd in self.read_fds or fd in self.write_fds or fd in self.error_fds:
            raise IOError("fd %s already registered" % fd)
        if events & select.EPOLLIN:
            self.read_fds.add(fd)
        if events & select.EPOLLOUT:
            self.write_fds.add(fd)
        if events & select.EPOLLERR:
            self.error_fds.add(fd)
            # Closed connections are reported as errors by epoll and kqueue,
            # but as zero-byte reads by select, so when errors are requested
            # we need to listen for both read and error.
            # self.read_fds.add(fd)

    def modify(self, fd, events):
        self.unregister(fd)
        self.register(fd, events)

    def unregister(self, fd):
        self.read_fds.discard(fd)
        self.write_fds.discard(fd)
        self.error_fds.discard(fd)

    def poll(self, timeout):
        readable, writeable, errors = select.select(
            self.read_fds, self.write_fds, self.error_fds, timeout)
        events = {}
        for fd in readable:
            events[fd] = events.get(fd, 0) | select.EPOLLIN
        for fd in writeable:
            events[fd] = events.get(fd, 0) | select.EPOLLOUT
        for fd in errors:
            events[fd] = events.get(fd, 0) | select.EPOLLERR
        return events.items()