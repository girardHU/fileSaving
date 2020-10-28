#!/usr/bin/env python3

import sys
import time
from custom_sockets_api import ServerSocket


host = sys.argv[1]
port = int(sys.argv[2])
time.sleep(5)
server = ServerSocket(host, port)
