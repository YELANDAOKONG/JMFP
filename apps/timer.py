#!/bin/python3
from datetime import datetime
import time
import json
from libmfpc import *

class MFPClientExtended(MFPClient):
    def send_time_message(self):
        current_time = datetime.now()
        message = {
            "type": "time",
            "date": {
                "y": current_time.year,
                "m": current_time.month,
                "d": current_time.day,
                "h": current_time.hour,
                "m": current_time.minute,
                "s": current_time.second
            },
            "tick": {
                "n": int(time.time()),
                "m": int(time.time()) + 946684800
            }
        }
        return self.send_message(message)

client = MFPClientExtended('127.0.0.1', 20035, 'your_password')
if client.connect():
    while True:
        if client.send_time_message():
            print("[~] Time message sent successfully.")
        time.sleep(30)
else:
    print("[^] Failed to connect to the server.")

