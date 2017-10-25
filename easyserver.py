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
    def __init__(self):
        pass
    pass

class esayLoop():
    pass

def run(environ, start_response):
    # server = easyHttpServer()
    res = socket.getaddrinfo("0.0.0.0",8000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 6)
    sock.bind(("0.0.0.0",8000))
    sock.listen(1)
    my_accept(sock, 6, daemon=False)

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

