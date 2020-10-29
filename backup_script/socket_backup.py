#!/usr/bin/env python3

import time
import os
from modules.custom_sockets_api import ClientSocket
import check as b_script

notification_host = os.environ.get("NOTIFICATION_HOST")
userClient = ClientSocket(notification_host, 56235)
print("client user initiated")

userClient.custom_send("User_connect")
time.sleep(1)
while True:
    try:
        recved = userClient._sock.recv(1024)
        print(recved)
        if recved == b"":
            userClient.close_socket()
            break
        else:
            b_script.run_check()
            pass
    except KeyboardInterrupt:
        print("caught KeyboardInterrupt, exiting")
        userClient.close_socket()
        break
