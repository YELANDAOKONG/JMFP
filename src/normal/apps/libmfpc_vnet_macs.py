#!/bin/python3
from datetime import datetime
import time
import json
from libmfpc import *
from libmfpc_vnet import *

if __name__ == "__main__":
    client = MFPClientExtended('127.0.0.1', 20035, 'passwd')
    print("[+] Connecting to the server...")
    if client.connect():
        print("[$] Connected to the server.")
        while True:
            client.receive_vnet_message("all")
            pass
    else:
        print("[^] Failed to connect to the server.")
    print("[-] Stopping the client.")
    sys.exit()

