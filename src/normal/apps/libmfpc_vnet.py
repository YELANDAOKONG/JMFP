#!/bin/python3
from datetime import datetime
import time
import json
from libmfpc import *
import uuid
import sys
import hashlib

class MFPClientExtended(MFPClient):
    VMAC_LEN = 32
    def get_vmac(self,address:tuple) -> str:
        return hashlib.md5(f"{address}".encode()).hexdigest()

    def get_self_vmac(self) -> str:
        temp_id = uuid.uuid4().hex
        message = {
            "type": "vnet.vmac",
            "todo": "get_vmac",
            "uuid": temp_id,
        }
        self.send_message(message)
        while True:
            response = self.receive_message()
            if not "data" in response:
                continue
            data = response["data"]
            if not ("type" in data and data["type"] == "vnet.vmac"):
                continue
            if not ("todo" in data and data["todo"] == "set_vmac"):
                continue
            if not ("uuid" in data and data["uuid"] == temp_id):
                continue
            if not ("vmac" in data):
                continue
            return data["vmac"]

    def send_vnet_message(self, from_vmac:str, to_vmac:str, message: dict):
        message = {
            "type": "vnet.msg",
            "from": from_vmac,
            "to": to_vmac,
            "data": message,
        }
        self.send_message(message)
        return
    
    def receive_vnet_message(self, vmac:str) -> tuple:
        while True:
            response = self.receive_message()
            if not "data" in response:
                continue
            if not "addr" in response:
                continue
            data = response["data"]
            addr = response["addr"]
            if not ("type" in data and data["type"] == "vnet.msg"):
                if not ("type" in data and data["type"] == "vnet.vmac"):
                    continue
                if not ("todo" in data and data["todo"] == "get_vmac"):
                    continue
                if not ("uuid" in data):
                    continue
                temp_id = data["uuid"]
                temp_vmac = self.get_vmac(addr)
                message = {
                    "type": "vnet.vmac",
                    "todo": "set_vmac",
                    "uuid": temp_id,
                    "vmac": temp_vmac
                }
                self.send_message(message)
                continue
            if not ("from" in data and len(data['from']) == self.VMAC_LEN):
                continue
            if not ("to" in data and (len(data['from']) == self.VMAC_LEN or data['from'] == "all")):
                continue
            if not ("data" in data):
                continue
            data_from = data["from"]
            data_to = data["to"]
            data_data = data["data"]
            if not (data_to == vmac or data_to == "all") and vmac != "all":
                continue
            return data_from, data_to, data_data


if __name__ == "__main__":
    client = MFPClientExtended('127.0.0.1', 20035, 'passwd')
    print("[+] Connected to the server.")
    if client.connect():
        while True:
            client.receive_vnet_message("all")
    else:
        print("[^] Failed to connect to the server.")
    print("[-] Stopping the client.")
    sys.exit()

