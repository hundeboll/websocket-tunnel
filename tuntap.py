#!/usr/bin/env python2

import os
import sys
import fcntl
import struct
import logging

TUN_KO_PATH = "/dev/net/tun"
TUNSETIFF   = 0x400454ca
IFF_TUN     = 0x0001
IFF_TAP     = 0x0002
IFNAMSIZ    = 16

class tuntap(object):

    def __init__(self, name = ""):
        self.name = name
        self._fd = os.open(TUN_KO_PATH, os.O_RDWR)

        if "tap" in name:
            mode = IFF_TAP
        else:
            mode = IFF_TUN

        if not name[-1:].isdigit():
            name = ""

        logging.info("Opening {}".format(name))

        try:
            ifr = struct.pack("{}sh".format(IFNAMSIZ), name, mode)
            ret = fcntl.ioctl(self._fd, TUNSETIFF, ifr)
        except IOError as e:
            if e.errno == 1:
                logging.error("Operation not permitted")
            return

        if name == "":
            self.name = struct.unpack("{}s".format(IFNAMSIZ), ret[:IFNAMSIZ])

        logging.info("Opened {}".format(self.name))

    @property
    def fd(self):
        return self._fd

if __name__ == "__main__":
    if len(sys.argv) > 1:
        t = tuntap(name=sys.argv[1])
    else:
        t = tuntap()
        t = tuntap("tap")
