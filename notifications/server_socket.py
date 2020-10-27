#!/usr/bin/env python3

import sys
import time
import socket
import selectors
import types


class ServerSocket:
    def __init__(self, host, port):
        self._lsock = None
        self._sel = selectors.DefaultSelector()
        # self._addr = None
        self.start_server(host, port)

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print("accepted connection from", addr)
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self._sel.register(conn, events, data=data)

    def service_connection(self, key, mask):
        # print("key:", key)
        # print("mask:", mask)
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            print("recv_data:", recv_data)
            time.sleep(1)
            if recv_data is b'User_connect':
                self.handle_user(sock)
            elif recv_data is b'Admin_connect':
                self.handle_admin(sock)
            elif recv_data
            is b'File_update'
            or b'File_delete'
            or b'File_create':
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

    def handle_user(self, sock):
        print("handle_user")

    def handle_admin(self, sock):
        print("handle_admin")

    def handle_api_ping(self, ping):
        print("handle_api_ping, ping:", ping)

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
