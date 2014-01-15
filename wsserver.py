#!/usr/bin/env python2

from gevent import monkey; monkey.patch_all()
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
from gevent import os
import argparse
import gevent
import tuntap
import sys

p = argparse.ArgumentParser(description='Send and receive data from a websocket server')

p.add_argument('-d', '--src',
        type=str,
        default='127.0.0.1',
        help='host to listen on')

p.add_argument('-p', '--port',
        type=int,
        default=8080,
        help='port number to listen on')

p.add_argument('-l', '--loc',
        type=str,
        default='/',
        help='path to request from server')

p.add_argument('-t', '--tuntap',
        type=str,
        default="",
        help='\'tap\' for tap mode or interface to use'
        )

args = p.parse_args()

class server(WebSocketApplication):
    tuntap = None

    def read_fd(self):
        while True:
            try:
                msg = os.tp_read(self.tuntap.fd, 1500)
                if not msg:
                    break
            except IOError:
                break
            if self.ws.closed:
                break
            self.ws.send(msg, True)

    def on_open(self):
        self.reader = gevent.spawn(self.read_fd)

    def on_close(self, reason):
        if (hasattr(self, 'reader')):
            self.reader.kill()

    def on_message(self, msg):
        if not msg:
            return
        os.tp_write(self.tuntap.fd, msg)

if __name__ == "__main__":
    server.tuntap = tuntap.tuntap(args.tuntap)
    wss = WebSocketServer((args.src, args.port), Resource({args.loc: server}))

    try:
        wss.serve_forever()
    except KeyboardInterrupt:
        wss.close()
