# -*- coding:utf-8 -*-
import re
from argparse import ArgumentParser
from easyserver import easyHttpServer


naiveip_re = re.compile(r"""^(?:
(?P<addr>
    (?P<ipv4>\d{1,3}(?:\.\d{1,3}){3}) |         # IPv4 address
    (?P<ipv6>\[[a-fA-F0-9:]+\]) |               # IPv6 address
    (?P<fqdn>[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*) # FQDN
):)?(?P<port>\d+)$""", re.X)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-r', '--runserver', type=str, help='start the server host:post')
    args = parser.parse_args()
    address = args.runserver
    if not address:
        address = "0.0.0.0:8000"
    address = re.match(naiveip_re, address)
    address =  address.groupdict()
    return address["addr"], int(address["port"])

def main():
    app = easyHttpServer(parse_args())
    app.start()

if __name__ == "__main__":
    main()
