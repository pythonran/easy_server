# coding=utf8
import socket
import os
import sys
from eventloop import eventLoop
from utils import async



handler_proto_event = {
    "IPPROTO_IP": [()],

}


class easyHandler():

    def IPPROTO_IP(self):
        pass

    def IPPROTO_UDP(self):
        pass

    def IPPROTO_TCP(self):
        pass


class easyHttpServer(object):
    def __init__(self, addrs):
        self.listensock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 6)
        self.listensock.bind(addrs)
        self.listensock.listen(1)
        self.fd_to_socket = {str(self.listensock.fileno()): self.listensock}
        self.IOloop = eventLoop(self.listensock)
        self.start()

    def start(self):
        while True:
            print "等待活动连接......"
            # 轮询注册的事件集合，返回值为[(文件句柄，对应的事件)，(...),....]
            events = self.IOloop.loop.poll(5)
            if not events:
                print "epoll超时无活动连接，重新轮询......"
                continue
            print "有", len(events), "个新事件，开始处理......"
            print events
            for fd, event in events:
                sock = self.fd_to_socket[fd]
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
                    # message_queues[connection] = Queue.Queue()
                # 关闭事件
                elif event & self.IOloop.EPOLLHUP:
                    print 'client close'
                    # 在epoll中注销客户端的文件句柄
                    self.IOloop.loop.unregister(fd)
                    # 关闭客户端的文件句柄
                    self.fd_to_socket[fd].close()
                    # 在字典中删除与已关闭客户端相关的信息
                    del self.fd_to_socket[fd]
                # 可读事件
                elif event & self.IOloop.EPOLLIN:
                    # 接收数据
                    data = sock.recv(1024)
                    # data = sock.makefile("r")
                    if data:
                        print "收到数据：", data, "客户端：", sock.getpeername()
                        # 将数据放入对应客户端的字典
                        message_queues[sock].put(
                            "HTTP/1.0 200 OK\r\nheaders:1\r\nContent-Length:16000\r\n\r\n{}\r\n\r\n".format(
                                "r" * 16000))
                        # 修改读取到消息的连接到等待写事件集合(即对应客户端收到消息后，再将其fd修改并加入写事件集合)
                        self.IOloop.loop.modify(fd, select.EPOLLOUT)
                    else:
                        self.IOloop.loop.modify(fd, select.EPOLLHUP)
                # 可写事件
                elif event & self.IOloop.EPOLLOUT:
                    try:
                        # 从字典中获取对应客户端的信息
                        msg = message_queues[sock].get_nowait()
                    except Queue.Empty:
                        print sock.getpeername(), " queue empty"
                        # 修改文件句柄为读事件
                        self.IOloop.loop.modify(fd, select.EPOLLHUP)
                    else:
                        print "发送数据：", msg, "客户端：", sock.getpeername()
                        # 发送数据
                        sock.send(msg)
                else:
                    print "event:", event
                    # 在epoll中注销服务端监听文件句柄
                    self.IOloop.loop.unregister(self.listensock.fileno())
                    # 关闭epoll
                    self.IOloop.loop.close()
                    # 关闭服务器socket
                    self.listensock.close()
            pass
        pass
class esayLoop():
    pass


def run(addr, handler):
    while True:
        print "等待活动连接......"
        # 轮询注册的事件集合，返回值为[(文件句柄，对应的事件)，(...),....]
        events = epoll.poll(timeout)
        if not events:
            print "epoll超时无活动连接，重新轮询......"
            continue
        print "有", len(events), "个新事件，开始处理......"
        print events
        for fd, event in events:
            sock = fd_to_socket[fd]
            # 如果活动socket为当前服务器socket，表示有新连接
            if sock == serversocket:
                connection, address = serversocket.accept()
                print "新连接：", address
                # 新连接socket设置为非阻塞
                connection.setblocking(False)
                # 注册新连接fd到待读事件集合
                epoll.register(connection.fileno(), select.EPOLLIN)
                # 把新连接的文件句柄以及对象保存到字典
                fd_to_socket[connection.fileno()] = connection
                # 以新连接的对象为键值，值存储在队列中，保存每个连接的信息
                message_queues[connection] = Queue.Queue()
            # 关闭事件
            elif event & select.EPOLLHUP:
                print 'client close'
                # 在epoll中注销客户端的文件句柄
                epoll.unregister(fd)
                # 关闭客户端的文件句柄
                fd_to_socket[fd].close()
                # 在字典中删除与已关闭客户端相关的信息
                del fd_to_socket[fd]
            # 可读事件
            elif event & select.EPOLLIN:
                # 接收数据
                data = sock.recv(1024)
                # data = sock.makefile("r")
                if data:
                    print "收到数据：", data, "客户端：", sock.getpeername()
                    # 将数据放入对应客户端的字典
                    message_queues[sock].put(
                        "HTTP/1.0 200 OK\r\nheaders:1\r\nContent-Length:16000\r\n\r\n{}\r\n\r\n".format(
                            "r" * 16000))
                    # 修改读取到消息的连接到等待写事件集合(即对应客户端收到消息后，再将其fd修改并加入写事件集合)
                    epoll.modify(fd, select.EPOLLOUT)
                else:
                    epoll.modify(fd, select.EPOLLHUP)
            # 可写事件
            elif event & select.EPOLLOUT:
                try:
                    # 从字典中获取对应客户端的信息
                    msg = message_queues[sock].get_nowait()
                except Queue.Empty:
                    print sock.getpeername(), " queue empty"
                    # 修改文件句柄为读事件
                    epoll.modify(fd, select.EPOLLHUP)
                else:
                    print "发送数据：", msg, "客户端：", sock.getpeername()
                    # 发送数据
                    sock.send(msg)
            else:
                print "event:", event
                # 在epoll中注销服务端文件句柄
                epoll.unregister(serversocket.fileno())
                # 关闭epoll
                epoll.close()
                # 关闭服务器socket
                serversocket.close()


@async
def my_accept(sock, proto, daemon=False):
    while True:
        conn_sock, addrinfo = sock.accept()
        # proto_sock[str(proto)] = conn_sock
        rf = conn_sock.makefile(mode="r")
        line = rf.readline()
        total_context = ""
        total_context += context
        while context != "\r\n":
            context = rf.readline()
            total_context += context
            print total_context
        print context, addrinfo

