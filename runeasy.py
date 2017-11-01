# -*- coding:utf-8 -*-
import select
import Queue
import socket
import re
from argparse import ArgumentParser

# serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
# # 设置IP地址复用
# serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# # ip地址和端口号
# server_address = ("0.0.0.0", 8888)
# # 绑定IP地址
# serversocket.bind(server_address)
# # 监听，并设置最大连接数
# serversocket.listen(10)
# print  "服务器启动成功，监听IP：", server_address
# # 服务端设置非阻塞
# serversocket.setblocking(False)
# # 超时时间
# timeout = 10
# # 创建epoll事件对象，后续要监控的事件添加到其中
# epoll = select.epoll()
# # 注册服务器监听fd到等待读事件集合
# epoll.register(serversocket.fileno(), select.EPOLLIN)
# # 保存连接客户端消息的字典，格式为{}
# message_queues = {}
# # 文件句柄到所对应对象的字典，格式为{句柄：对象}
# fd_to_socket = {serversocket.fileno(): serversocket, }

naiveip_re = re.compile(r"""^(?:
(?P<addr>
    (?P<ipv4>\d{1,3}(?:\.\d{1,3}){3}) |         # IPv4 address
    (?P<ipv6>\[[a-fA-F0-9:]+\]) |               # IPv6 address
    (?P<fqdn>[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*) # FQDN
):)?(?P<port>\d+)$""", re.X)

class Server(object):
    def runt(self):
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

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('runserver', type=str, help='start the server host:post')
    args = parser.parse_args()
    address = args.runserver
    if not address:
        address = "0.0.0.0:8000"
    address = re.match(naiveip_re, address)
    address =  address.groupdict()
    return address["addr"], address["port"]



if __name__ == "__main__":
    parse_args()
