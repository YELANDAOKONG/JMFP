#!/bin/python3
import socket
import json
import time
import hashlib
import ubinascii

class MFPClient:
    def __init__(self, host='localhost', port=20035, password='', time_offset=946684800):
        self.host = host
        self.port = port
        self.password = password
        self.time_offset = time_offset
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            auth_data = {'auth': self.get_signature()}
            self.client_socket.send(json.dumps(auth_data).encode())
            response = self.client_socket.recv(4096)
            # print(response)
            response_data = json.loads(response.decode())
            if response_data.get('code') == 200:
                return True
            else:
                self.client_socket.close()
                return False
        except Exception as e:
            print(f"[^] Connection error: {e}")
            return False

    def get_signature(self):
        timestamp = str(int(time.time()) + self.time_offset)
        data = timestamp[:8] + self.password + timestamp[:8]
        hashed_data = hashlib.sha256(data.encode()).digest()
        hashed_data_hex = ubinascii.hexlify(hashed_data).decode()
        return hashed_data_hex

    def send_message(self, message):
        try:
            # self.client_socket.send(message.encode())
            # response = self.client_socket.recv(4096)
            # return response.decode()
            self.client_socket.send(json.dumps(message).encode())
            return True
        except Exception as e:
            print(f"[^] Message sending error: {e}")
            return False
    
    def receive_message(self):
        try:
            while True:
                try:
                    response = self.client_socket.recv(4096)
                    data = response.decode()
                    json_data = json.loads(data)
                    if "keep" in json_data:
                        if json_data["keep"] == True:
                            continue
                    return json_data
                except ValueError:
                    continue
        except Exception as e:
            print(f"[^] Message receiving error: {e}")
            return None

    def close(self):
        self.client_socket.close()

