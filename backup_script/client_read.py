#!/usr/bin/env python3

import time
from custom_sockets_api import ClientSocket
import backup_script as b_script


userClient = ClientSocket("0.0.0.0", 9983)
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