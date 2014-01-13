#!/usr/bin/env python2

from gevent.fileobject import FileObjectThread
from gevent import monkey; monkey.patch_all()
from websocket import WebSocket
import websocket
import argparse
import gevent
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

args = p.parse_args()

class client(object):
    stdin = FileObjectThread(sys.stdin)
    stdout = FileObjectThread(sys.stdout)
    reader_func = None
    sender_func = None
    stopping = False
    greenlets = None

    def __init__(self, args, url):
        self.args = args

        self.ws = WebSocket()
        self.ws.connect(url)

        if args.ascii:
            self.reader_func = self.stdin.readline
            self.sender_func = self.ws.send
        else:
            self.reader_func = self.stdin.read
            self.sender_func = self.ws.send_binary

        self.greenlets = [
            gevent.spawn(self.read_ws),
            gevent.spawn(self.write_ws)
        ]

    def write_ws(self):
        while not self.stopping:
            try:
                msg = self.reader_func(20000)
                if not self.ws.connected:
                    break
                if not msg:
                    self.stopping = True
                    self.ws.close()
                    break
            except IOError:
                break
            self.sender_func(msg)

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
            self.stdout.write(bytes(msg))
            self.stdout.flush()

    def join(self):
        gevent.joinall(self.greenlets)


args.ssl = 's' if args.ssl else ''
url = "ws{ssl}://{dst}:{port}{loc}".format(**vars(args))
websocket.enableTrace(False)

try:
    c = client(args, url)
    c.join()
except KeyboardInterrupt:
    c.ws.close()
