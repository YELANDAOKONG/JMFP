#!/bin/python3
from datetime import datetime
import time
import json
from libmfpc import *
from libmfpc_vnet import *

while_mode = False
if __name__ == "__main__":
    client = MFPClientExtended('127.0.0.1', 20035, 'passwd')
    print("[+] Connecting to the server...")
    if client.connect():
        print("[%] Connected to the server.")
        print("[>] Type 'exit' to stop the client, type 'mac' to get the vmac, type 'while' to enable while mode.")
        while True:
            try:
                if while_mode:
                    data_from, data_to, data_data = client.receive_vnet_message("all")
                    print(f"[#] Message >>> {data_from} -> {data_to} :> {data_data}")
                    continue

                message = input("> ")
                if message.lower().strip() == "exit" or message.lower().strip() == "quit" or message.lower().strip() == "q":
                    print("[-] Stopping the client.")
                    client.close()
                    sys.exit()
                    break
                if message.lower().strip() == "mac" or message.lower().strip() == "vmac" or message.lower().strip() == "m":
                    print(f"[$] Client VMAC: {client.get_self_vmac()}")
                    continue
                if message.lower().strip() == "while" or message.lower().strip() == "w":
                    while_mode = True
                    print("[!] While mode enabled.")
                    continue
                try:
                    json_message = json.loads(message)
                    if 'from' not in json_message:
                        print(f"[!] Invalid JSON Data: 'from' field not found")
                        continue
                    if 'to' not in json_message:
                        print(f"[!] Invalid JSON Data: 'to' field not found")
                        continue
                    if 'data' not in json_message:
                        print(f"[!] Invalid JSON Data: 'data' field not found")
                        continue
                    client.send_vnet_message(
                        json_message['from'],
                        json_message['to'],
                        json_message['data']
                    )
                    continue
                except json.JSONDecodeError as je:
                    print(f"[!] Invalid JSON Format")
                    continue
            except Exception as ex:
                print(f"[^] Catched exception: {ex}")
                print("[-] Stopping the client.")
                client.close()
                sys.exit()
                break
    else:
        print("[^] Failed to connect to the server.")
    print("[-] Stopping the client.")
    sys.exit()

