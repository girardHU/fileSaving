#!/usr/bin/env python3

import sys
import time
import socket
import traceback
import selectors
import types

messages = {
    b"File_update": "Notify_File_update",
    b"File_delete": "Notify_File_delete",
    b"File_create": "Notify_File_create"
}


class ServerSocket:
    def __init__(self, host, port):
        self._lsock = None
        self._sel = selectors.DefaultSelector()
        self._counter = 0
        self.start_server(host, port)

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print("accepted connection from", addr)
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"")
        self._sel.register(conn, selectors.EVENT_READ, data=data)

    def service_connection(self, key, mask):
        # print("key:", key)
        # print("mask:", mask)
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            self._counter += 1
            recv_data = sock.recv(1024)  # Should be ready to read
            # print(f"{self._counter} iteration")
            print("recv_data:", recv_data, "from", data.addr)
            # time.sleep(1)
            if recv_data == b"User_connect":
                self.handle_user(key)
            elif recv_data == b"Admin_connect":
                self.handle_user(key)
            elif recv_data in messages.keys():
                self.handle_api_ping(recv_data)
            else:
                print("closing connection to", data.addr)
                self._sel.unregister(sock)
                sock.close()
        # if mask & selectors.EVENT_WRITE:
        #     if data.outb:
        #         print("echoing", repr(data.outb), "to", data.addr)
        #         sent = sock.send(data.outb)  # Should be ready to write
        #         data.outb = data.outb[sent:]

    def handle_user(self, key):
        print("handle_user")
        sock = key.fileobj
        self._sel.unregister(sock)
        data = types.SimpleNamespace(addr=key.data.addr, outb=b"")
        self._sel.register(sock, selectors.EVENT_WRITE, data=data)

    def handle_api_ping(self, message):
        print("handle_api_ping, ping:", message, "\n")
        events = self._sel.select(timeout=None)
        for key, mask in events:
            sock = key.fileobj
            if mask & selectors.EVENT_WRITE:
                print("sending", messages.get(message), "to", key.data.addr)
                sent = sock.send(messages.get(message).encode())

    def start_server(self, host, port):
        self._lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._lsock.bind((host, port))
        self._lsock.listen()
        print("listening on", (host, port))
        self._lsock.setblocking(False)
        self._sel.register(self._lsock, selectors.EVENT_READ, data=None)

        try:
            while True:
                events = self._sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self._sel.close()


class ClientSocket:
    def __init__(self, addr, port):
        self._sock = None
        self._addr = None
        self.init_connection(addr, port)

    def init_connection(self, host, port):
        addr = (host, port)
        print("starting connection to", addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr)
        self._addr = addr
        self._sock = sock
        print("connected")

    def custom_send(self, message):
        totalsent = 0
        print("message length:", len(message))
        while totalsent < len(message):
            sent = self._sock.send(message[totalsent:].encode())
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent
        print("total sent:", totalsent, "\n")

    def custom_read(self):
        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = self._sock.recv(min(MSGLEN - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk.decode())
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)

    def close_socket(self):
        self._sock.close()
