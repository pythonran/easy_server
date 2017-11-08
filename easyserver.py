# coding=utf8
import socket
import os
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
    pass

class easyResponse():
    def __init__(self, content_type, charset):
        self._headers = {}
        self._headers["Server"] = "easysever/1.0"
        self._headers["Content-type"] = content_type + ";" + charset
        pass

    __repr__ = lambda self: self._headers
    __getitem__ = lambda self, header: self._headers[header]
    __setitem__ = lambda self, header, value: self._headers.update(header=value)

    def set_cookie(self):
        pass
    pass

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
        self.__response = {}
        self.init_url_view(self.url_view)
        self.fd_to_socket = {str(self.listensock.fileno()): self.listensock}
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
            # 轮询注册的事件集合，返回值为[(文件句柄，对应的事件)，(...),....]
            events = self.IOloop.loop.poll(10)
            if not events:
                print "epoll超时无活动连接，重新轮询......"
                continue
            print "有", len(events), "个新事件，开始处理......"
            for fd, event in events:
                sock = self.fd_to_socket[str(fd)]
                # 如果活动socket为当前服务器socket，表示有新连接
                if sock == self.listensock:
                    connection, address = self.listensock.accept()
                    print "新连接：", address
                    # 新连接socket设置为非阻塞
                    connection.setblocking(False)
                    # 注册新连接fd到待读事件集合
                    self.IOloop.loop.register(connection.fileno(), self.IOloop.EPOLLIN)
                    # 把新连接的文件句柄以及对象保存到字典
                    self.fd_to_socket[connection.fileno()] = connection
                    # 以新连接的对象为键值，值存储在队列中，保存每个连接的信息
                    self.__response[connection] = Queue.Queue()
                # 关闭事件
                elif event & self.IOloop.EPOLLHUP:
                    print fd, 'client close'
                    # 在epoll中注销客户端的文件句柄
                    self.IOloop.loop.unregister(fd)
                    # 关闭客户端的文件句柄
                    self.fd_to_socket[fd].close()
                    # 在字典中删除与已关闭客户端相关的信息
                    del self.fd_to_socket[fd]
                # 可读事件
                elif event & self.IOloop.EPOLLIN:
                    # 接收数据
                    # data = sock.recv(1024)
                    self.thread_pool.queueTask(process_request, args=(self, fd, sock))

                # 可写事件
                elif event & self.IOloop.EPOLLOUT:
                    try:
                        # 从字典中获取对应客户端的信息
                        # msg = self.__response[sock].get_nowait()
                        self.thread_pool.queueTask(process_response, args=(self, fd, sock))
                    except Queue.Empty:
                        print sock.getpeername(), " queue empty"
                        # 修改文件句柄为读事件
                        # self.IOloop.loop.modify(fd, self.IOloop.EPOLLHUP)
                    else:
                        pass

                else:
                    print "else event:", event
                    # 在epoll中注销服务端监听文件句柄
                    self.IOloop.loop.unregister(self.listensock.fileno())
                    # 关闭epoll
                    self.IOloop.loop.close()
                    # 关闭服务器socket
                    self.listensock.close()


def process_request(server, fd, sock):
    data = sock.makefile("r")
    first_line = data.readline()
    args = parse_request(first_line)
    if args:
        method, path, version = args
        hearders = parse_headers(data)
    else:
        server.IOloop.loop.modify(fd, server.IOloop.EPOLLHUP)
    if first_line:
        print "收到请求：", first_line, "客户端：", sock.getpeername()
        response = server.url_view["/"]()
        print "response:", response
        server.__response[sock].put(response)
        server.IOloop.loop.modify(fd, server.IOloop.EPOLLOUT)
    else:
        server.IOloop.loop.modify(fd, server.IOloop.EPOLLHUP)

def process_response(server, fd, sock):
    wfile = sock.makefile("w")
    response = server.__response
    httpline = "HTTP/1.1 200 OK\r\n"
    response_headers = {
        "Content-Length": len(server.__response[fd].get())
    }
    response = httpline + ''.join(['%s: %s\r\n' % (k, v) for k, v in response_headers.items()]) + '\r\n' + response
    wfile.write(response)
    print "response:", response
    server.IOloop.loop.modify(fd, server.IOloop.EPOLLHUP)

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
    requestline = first_line
    path = ""
    requestline = requestline.rstrip('\r\n')
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
    return command, path, version

def parse_headers(headerfile):
    _headers = {}
    line = headerfile.readline()
    if line == "\r\n" or not line:
        return False
    _headers.update({line.split(":")[0]: line.split(":")[1]})
    while True:
        line = headerfile.readline()
        print line.split(":")
        if line == "\r\n" or not line:
            break
        _headers.update({line.split(":")[0]: line.split(":")[1]})
    return _headers

