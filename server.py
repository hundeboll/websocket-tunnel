#!/usr/bin/env python2

from gevent import monkey; monkey.patch_all()
from gevent.fileobject import FileObjectPosix
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
import argparse
import gevent
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

args = p.parse_args()

class server(WebSocketApplication):
    stdin = FileObjectPosix(sys.stdin, close=False)
    stdout = FileObjectPosix(sys.stdout, close=False)
    reader_func = None

    def write_ws(self):
        while True:
            try:
                msg = self.reader_func(20000)
                if not msg:
                    break
            except IOError:
                break
            if self.ws.closed:
                break
            self.ws.send(msg, True)

    def on_open(self):
        self.reader = gevent.spawn(self.write_ws)

    def on_close(self, reason):
        if (hasattr(self, 'reader')):
            self.reader.kill()

    def on_message(self, msg):
        if not msg:
            return
        self.stdout.write(msg)
        self.stdout.flush()

if args.ascii:
    server.reader_func = server.stdin.readline
else:
    server.reader_func = server.stdin.read

wss = WebSocketServer((args.src, args.port), Resource({args.loc: server}))

try:
    wss.serve_forever()
except KeyboardInterrupt:
    wss.close()
