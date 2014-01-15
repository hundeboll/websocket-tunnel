#!/usr/bin/env python2

from gevent import monkey; monkey.patch_all()
from gevent import os
from websocket import WebSocket
import websocket
import argparse
import gevent
import tuntap
import sys

p = argparse.ArgumentParser(description='Send and receive data from a websocket server')

p.add_argument('-d', '--dst',
        type=str,
        default='127.0.0.1',
        help='host to connect to')

p.add_argument('-p', '--port',
        type=int,
        default=8080,
        help='port number to connect to')

p.add_argument('-l', '--loc',
        type=str,
        default='/',
        help='path to request from server')

p.add_argument('-s', '--ssl',
        action='store_true',
        dest='ssl',
        help='enable ssl')

p.add_argument('-S', '--no-ssl',
        action='store_false',
        dest='ssl',
        help='disable ssl')

p.add_argument('-a', '--ascii',
        action='store_true',
        dest='ascii',
        default=True,
        help='send data as line by line (inefficient)')

p.add_argument('-b', '--binary',
        action='store_false',
        dest='ascii',
        help='send data as binary chunks')

p.add_argument('-t', '--tuntap',
        type=str,
        default="",
        help='\'tap\' for tap mode or interface to use')

args = p.parse_args()

class client(object):
    stopping = False
    greenlets = None

    def __init__(self, args, url):
        self.args = args

        self.tuntap = tuntap.tuntap(args.tuntap)

        self.ws = WebSocket()
        self.ws.connect(url)

        self.greenlets = [
            gevent.spawn(self.read_ws),
            gevent.spawn(self.read_fd)
        ]

    def read_fd(self):
        while not self.stopping:
            try:
                msg = os.tp_read(self.tuntap.fd, 1500)
                if not self.ws.connected:
                    break
                if not msg:
                    self.stopping = True
                    self.ws.close()
                    break
            except IOError:
                break
            self.ws.send_binary(msg)

    def read_ws(self):
        while not self.stopping:
            try:
                msg = self.ws.recv()
                if not msg:
                    break
            except websocket.WebSocketConnectionClosedException:
                self.stopping = True
                self.greenlets[1].kill()
                break
            except:
                continue
            os.tp_write(self.tuntap.fd, bytes(msg))

    def join(self):
        gevent.joinall(self.greenlets)


if __name__ == "__main__":
    args.ssl = 's' if args.ssl else ''
    url = "ws{ssl}://{dst}:{port}{loc}".format(**vars(args))

    try:
        c = client(args, url)
        c.join()
    except KeyboardInterrupt:
        c.ws.close()
