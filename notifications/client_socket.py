#!/usr/bin/env python3

import sys
import time
import socket
import traceback


class ClientSocket:
    def __init__(self, addr, port, mode):
        self._sock = None
        self._addr = None
        if mode is "r" or "w" or "rw" or "wr":
            self.mode = mode
        else:
            raise ValueError("wrong mode")
        self.init_connection(addr, port)

    def init_connection(self, host, port):
        addr = (host, port)
        print("starting connection to", addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr)
        self._addr = addr
        self._sock = sock
        print("conncted")

    def custom_send(self, message):
        if self.mode is "w" or "rw" or "wr":
            totalsent = 0
            print("message length:", len(message))
            while totalsent < len(message):
                sent = self._sock.send(message[totalsent:].encode())
                if sent == 0:
                    raise RuntimeError("socket connection broken")
                totalsent = totalsent + sent
            print("total sent:", totalsent)
        else:
            raise TypeError("wrong mode, you can't write")

    def custom_read(self, message):
        if self.mode is "r" or "rw" or "wr":
            chunks = []
            bytes_recd = 0
            while bytes_recd < MSGLEN:
                chunk = self._sock.recv(min(MSGLEN - bytes_recd, 2048))
                if chunk == b'':
                    raise RuntimeError("socket connection broken")
                chunks.append(chunk.decode())
                bytes_recd = bytes_recd + len(chunk)
            return b''.join(chunks)
        else:
            raise TypeError("wrong mode, you can't read")

    def close_socket(self):
        self._sock.close()
