# coding=utf8
import os
import sys
import socket
import Queue
import errno
import datetime
from eventloop import eventLoop
from handle_pool import  ThreadPool
from http_code import code_status


default_request_version = "HTTP/0.9"
protocol_version = "HTTP/1.0"

class easyRequest():
    def __init__(self, method, path, version, body=""):
        self.method = method.lower()
        self.headers = {}
        self._body = body
        self.path = path
        self.version = version

    @property
    def body(self):
        try:
            return eval(self._body)
        except:
            return self._body

    __repr__ = lambda self: self.version


class easyResponse():
    def __init__(self, body='', content_type="application/json", charset="utf-8", code=200):
        self.headers = {}
        self.code = str(code)
        self.headers["Server"] = "easysever/1.0"
        self.headers["Content-type"] = content_type + ";" + charset
        self.headers["Content-Length"] = len(body)
        self._body = body

    __getitem__ = lambda self, header: self._headers[header]
    __setitem__ = lambda self, header, value: self._headers.update(header=value)

    def set_cookie(self):
        pass

    @property
    def response(self):
        httpline = "HTTP/1.1 %s %s\r\n" % (self.code, code_status[self.code])
        return httpline + ''.join(['%s: %s\r\n' % (k, v) for k, v in self.headers.items()]) + "\r\n" + self._body


class easyHandler():
    @staticmethod
    def send_error(code, response):
        pass

    @classmethod
    def method_notallowed(cls, request):
        status_code = 405
        cur_response = easyResponse()
        cur_response.headers["Allow"] = 'Method Not Allowed (%s): %s' % (request.method, request.path)
        return cur_response.response


class easyHttpServer(object):

    def __init__(self, addrs):
        self.listensock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.listensock.setblocking(False)
        self.listensock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listensock.bind(addrs)
        self.listensock.listen(1)
        self.addrs = addrs
        self.url_view = {}
        self.response = {}
        self.init_url_view(self.url_view)
        self.fd_to_socket = {self.listensock.fileno(): self.listensock}
        self.processing = set()
        self.IOloop = eventLoop(self.listensock)
        self.thread_pool = ThreadPool(2)
        self.exit_msg = "\r\nBye!\r\n"

    def init_url_view(self, url_view_queue):
        from urls import URLMAPS
        for url, view_func in URLMAPS.items():
            self.url_view.update({url: view_func})

    def prity_print(self):
        print "Server at http://%s:%d/" % self.addrs
        print "Quit the server with CONTROL-C."

    def start(self):
        self.prity_print()
        try:
            while True:
                # print"等待活动连接......"
                events = self.IOloop.poll(10)
                if not events:
                    # print"epoll超时无活动连接，重新轮询......"
                    continue
                # print"有", len(events), "个新事件，开始处理......"
                for fd, event in events:
                    sock = self.fd_to_socket[fd]
                    if sock == self.listensock:
                        connection, address = self.listensock.accept()
                        # print"新连接：", address
                        connection.setblocking(False)
                        self.IOloop.add_event(connection.fileno(), self.IOloop.EPOLLIN)
                        self.fd_to_socket[connection.fileno()] = connection
                        self.response[connection.fileno()] = Queue.Queue()
                    elif event & self.IOloop.EPOLLHUP:
                        # printfd, 'EPOLLHUP'
                        self.IOloop.remove_event(fd)
                        self.fd_to_socket[fd].close()
                        del self.fd_to_socket[fd]
                        del self.response[fd]

                    elif event & self.IOloop.EPOLLIN:
                        # printfd, 'EPOLLIN'
                        self.IOloop.remove_event(fd)
                        self.thread_pool.queueTask(process_request, self, fd, sock)

                    elif event & self.IOloop.EPOLLOUT:
                        # printfd, 'EPOLLOUT'
                        self.IOloop.remove_event(fd)
                        self.thread_pool.queueTask(process_response, self, fd, sock)

                    else:
                        # printfd, "else event:", event
                        self.IOloop.remove_event(self.listensock.fileno())
                        self.IOloop.loop.close()
                        self.listensock.close()
        except socket.error as e:
            ERRORS = {
                errno.EACCES: "main You don't have permission to access that port.",
                errno.EADDRINUSE: "main That port is already in use.",
                errno.EADDRNOTAVAIL: "main That IP address can't be assigned to.",
                errno.EAGAIN: "main errno.EAGAIN"
            }
            try:
                error_text = ERRORS[e.errno]
                print "main error_text:",error_text
            except KeyError:
                print "main Error: %s" % str(e)
            sys.exit(1)
        except KeyboardInterrupt as err:
            for fd, sock in self.fd_to_socket.items():
                sock.close()
                if self.response.has_key(fd):
                    del self.response[fd]
            self.thread_pool.setThreadCount(0)
            sys.exit(self.exit_msg)

def process_request(server, fd, sock):
    rfile = sock.makefile("r")
    first_line = rfile.readline()
    request = parse_request(first_line)
    t = datetime.datetime.now()
    time_string = datetime.datetime.strftime(t, '%Y-%m-%d %H:%M:%S')
    if request:
        parse_headers(request, rfile)
    else:
        server.IOloop.update_event(fd, server.IOloop.EPOLLHUP)
    if first_line:
        data = server.url_view["/"](request)
        server.response[fd].put(data)
        server.IOloop.add_event(fd, server.IOloop.EPOLLOUT)
        print '''<{time}> "{method} {path} {version}" {code} {length}'''.format(time=time_string, method=request.method.upper(),
                path=request.path, version=request.version,code=data.code, length=len(data._body))
    else:
        server.IOloop.add_event(fd, server.IOloop.EPOLLHUP)
    rfile.close()

def process_response(server, fd, sock):
    current_response = server.response[fd].get(block=False)
    sock.sendall(current_response.response)
    server.IOloop.add_event(fd, server.IOloop.EPOLLHUP)
    sock.close()

def parse_request(first_line):
    """Parse a request (internal).

                The request should be stored in self.raw_requestline; the results
                are in self.command, self.path, self.request_version and
                self.headers.

                Return True for success, False for failure; on failure, an
                error is sent back.

    """
    command = None
    request_version = version = default_request_version
    close_connection = 1
    path = ""
    requestline = first_line.rstrip('\r\n')
    words = requestline.split()
    if len(words) == 3:
        command, path, version = words
        if version[:5] != 'HTTP/':
            easyHandler.send_error(400, "Bad request version (%r)" % version)
            return False
        try:
            base_version_number = version.split('/', 1)[1]
            version_number = base_version_number.split(".")
            if len(version_number) != 2:
                raise ValueError
            version_number = int(version_number[0]), int(version_number[1])
        except (ValueError, IndexError):
            easyHandler.send_error(400, "Bad request version (%r)" % version)
            return False
        if version_number >= (1, 1) and protocol_version >= "HTTP/1.1":
            close_connection = 0
        if version_number >= (2, 0):
            easyHandler.send_error(505,
                                   "Invalid HTTP Version (%s)" % base_version_number)
            return False
    elif len(words) == 2:
        command, path = words
        close_connection = 1
        if command != 'GET':
            easyHandler.send_error(400, "Bad HTTP/0.9 request type (%r)" % command)
            return False
    elif not words:
        return False
    else:
        easyHandler.send_error(400, "Bad request syntax (%r)" % requestline)
    return easyRequest(command, path, version)

def parse_headers(request, headerfile):
    line = headerfile.readline()
    if line == "\r\n" or not line:
        return False
    request.headers[line.split(":")[0]] = line.split(":")[1]
    while True:
        line = headerfile.readline()
        if line == "\r\n" or not line:
            break
        request.headers[line.split(":")[0]] = line.split(":")[1]


