# coding=utf8
import socket
import os
import time
import sys
from eventloop import eventLoop
from utils import async
import Queue
from handle_pool import  ThreadPool

handler_proto_event = {
    "IPPROTO_IP": [()],

}

default_request_version = "HTTP/0.9"
protocol_version = "HTTP/1.0"

class easyRequest():
    def __init__(self, method, path, version, headers={}, body=""):
        self.method = method.lower()
        self.headers = headers
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
    def __init__(self, body='', content_type="application/json", charset="utf-8"):
        self._headers = {}
        self._headers["Server"] = "easysever/1.0"
        self._headers["Content-type"] = content_type + ";" + charset
        self._headers["Content-Length"] = len(body)
        self._body = body

    __getitem__ = lambda self, header: self._headers[header]
    __setitem__ = lambda self, header, value: self._headers.update(header=value)

    def set_cookie(self):
        pass

    @property
    def response(self):
        httpline = "HTTP/1.1 200 OK\r\n"
        return httpline + ''.join(['%s: %s\r\n' % (k, v) for k, v in self._headers.items()]) + "\r\n" + self._body



class easyHandler():
    @staticmethod
    def send_error(code, response):
        pass

    def method_notallowed(self):
        """

        :rtype: object
        """
        status_code = 405
        return ""
        pass


class easyHttpServer(object):

    def __init__(self, addrs):
        self.listensock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 6)
        self.listensock.bind(addrs)
        self.listensock.listen(1)
        self.url_view = {}
        self.response = {}
        self.init_url_view(self.url_view)
        self.fd_to_socket = {self.listensock.fileno(): self.listensock}
        self.processing = set()
        self.IOloop = eventLoop(self.listensock)
        self.thread_pool = ThreadPool(2)
        self.start()

    def init_url_view(self, url_view_queue):
        from urls import URLMAPS
        for url, view_func in URLMAPS.items():
            self.url_view.update({url: view_func})

    def start(self):
        while True:
            print "等待活动连接......"
            events = self.IOloop.poll(10)
            if not events:
                print "epoll超时无活动连接，重新轮询......"
                continue
            print "有", len(events), "个新事件，开始处理......"
            for fd, event in events:
                sock = self.fd_to_socket[fd]
                if sock == self.listensock:
                    connection, address = self.listensock.accept()
                    print "新连接：", address
                    connection.setblocking(False)
                    self.IOloop.add_event(connection.fileno(), self.IOloop.EPOLLIN)
                    self.fd_to_socket[connection.fileno()] = connection
                    self.response[connection.fileno()] = Queue.Queue()
                elif event & self.IOloop.EPOLLHUP:
                    print fd, 'EPOLLHUP'
                    self.IOloop.remove_event(fd)
                    self.fd_to_socket[fd].close()
                    del self.fd_to_socket[fd]

                elif event & self.IOloop.EPOLLIN:
                    print fd, 'EPOLLIN'
                    self.thread_pool.queueTask(process_request, self, fd, sock)

                elif event & self.IOloop.EPOLLOUT:
                    print fd, 'EPOLLOUT'
                    self.thread_pool.queueTask(process_response, self, fd, sock)

                else:
                    print fd, "else event:", event
                    self.IOloop.remove_event(self.listensock.fileno())
                    self.IOloop.loop.close()
                    self.listensock.close()


def process_request(server, fd, sock):
    uid = str(fd) + str(server.IOloop.EPOLLIN)
    if uid in server.processing:
        return
    server.processing.add(uid)
    rfile = sock.makefile("r")
    first_line = rfile.readline()
    request = parse_request(first_line)
    if request:
        parse_headers(request, rfile)
    else:
        server.IOloop.update_event(fd, server.IOloop.EPOLLHUP)
    if first_line:
        print "收到请求：", first_line, "客户端：", sock.getpeername()
        data = server.url_view["/"](request)
        server.processing.discard(uid)
        server.response[fd].put(data)
        server.IOloop.update_event(fd, server.IOloop.EPOLLOUT)
    else:
        server.processing.discard(uid)
        server.IOloop.update_event(fd, server.IOloop.EPOLLHUP)
    rfile.close()

def process_response(server, fd, sock):
    uid = str(fd) + str(server.IOloop.EPOLLOUT)
    if uid in server.processing:
        return
    current_response = server.response[fd].get(block=False)
    sock.sendall(current_response.response)
    server.processing.discard(uid)
    server.IOloop.update_event(fd, server.IOloop.EPOLLHUP)

def parse_request(first_line):
    """Parse a request (internal).

                The request should be stored in self.raw_requestline; the results
                are in self.command, self.path, self.request_version and
                self.headers.

                Return True for success, False for failure; on failure, an
                error is sent back.

    """
    command = None  # set in case of error on the first line
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
            # RFC 2145 section 3.1 says there can be only one "." and
            #   - major and minor numbers MUST be treated as
            #      separate integers;
            #   - HTTP/2.4 is a lower version than HTTP/2.13, which in
            #      turn is lower than HTTP/12.3;
            #   - Leading zeros MUST be ignored by recipients.
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
        # print line.split(":")
        if line == "\r\n" or not line:
            break
        request.headers[line.split(":")[0]] = line.split(":")[1]


