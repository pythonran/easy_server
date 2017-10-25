import os

class parent(object):
    def __init__(self):
        print "parent"
    def server_forever(self):
        print "parent server_forerver"

class child(object):
    def __init__(self):
        print 'child'

    def server_forever(self):
        print "child server_forever"

if __name__ == "__main__":
    c = child()
    c.server_forever()