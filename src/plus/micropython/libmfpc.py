#!/bin/python3
# VERSION CODE
# => 2 / PLUS
# SUB VERSION CODE
# => 2
VERSION_CODE = 2
import socket
import select
import json
import time
import hashlib
import ubinascii
import ustruct



class MFPClient:
    def __init__(self, host='localhost', port=20035, password='', time_offset=946684800, MAX_PACKET_SIZE=1024 * 1024, PRINT_OUT=True, SOCKET_TIMEOUT=60):
        self.host = host
        self.port = port
        self.password = password
        self.time_offset = time_offset
        self.MAX_PACKET_SIZE = MAX_PACKET_SIZE
        self.PRINT_OUT = PRINT_OUT
        self.SOCKET_TIMEOUT = SOCKET_TIMEOUT
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _is_socket_closed(self, client_socket) -> bool:
        fileno = client_socket.fileno()
        readable, _, _ = select.select([client_socket], [], [], 0)
        return fileno not in [sock.fileno() for sock in readable]
    
    def _get_signature(self) -> str:
        timestamp = str(int(time.time()) + self.time_offset)
        data = timestamp[:8] + self.password + timestamp[:8]
        hashed_data = hashlib.sha256(data.encode()).digest()
        hashed_data_hex = ubinascii.hexlify(hashed_data).decode()
        return hashed_data_hex
    
    def get_signature(self) -> str:
        return self._get_signature()
    
    def _send_data(self, data:bytes) -> bool:
        try:
            data_length = len(data)
            # header = data_length.to_bytes(4, byteorder='big')
            header = ustruct.pack(">I", data_length)
            self.client_socket.send(header)
            self.client_socket.send(data)
            return True
        except Exception as e:
            if self.PRINT_OUT:
                # print(f"[^] Error sending data: {e}")
                pass
            return False
    
    def _recv_data(self) -> bytes:
        try:
            # self.client_socket.settimeout(self.SOCKET_TIMEOUT)
            header = self.client_socket.recv(4)
            # data_length = int.from_bytes(header, byteorder='big')
            data_length = ustruct.unpack(">I", header)[0]
            # if data_length > self.MAX_PACKET_SIZE:
            #     self.client_socket.close()
            #     return b""
            data = self.client_socket.recv(data_length)
            return data
        # except socket.timeout as se:
        #     if self.PRINT_OUT:
        #         # print(f"[^] The client {address} timed out. Closing the connection.")
        #         pass
        #     return b""
        except Exception as e:
            if self.PRINT_OUT:
                # print(f"[^] An error occurred while handling the server: {e}")
                pass
            return b""
        finally:
            # self.client_socket.close()
            # return b""
            pass
    
    def _send_keepalive(self):
        self.send_message_raw(
            {
                "type": "keepalive",
                "keep": True
            }
        )
        return
    
    def send_keepalive(self):
        self._send_keepalive()
        return

    def connect(self) -> bool:
        try:
            self.client_socket.settimeout(self.SOCKET_TIMEOUT)
            self.client_socket.connect((self.host, self.port))
            auth_data = {'auth': self._get_signature()}
            # self.client_socket.send(json.dumps(auth_data).encode())
            self._send_data(json.dumps(auth_data).encode())
            # response = self.client_socket.recv(4096)
            response = self._recv_data()
            if not response or response == b"":
                return False
            response_data = json.loads(response.decode())
            if response_data.get('code') == 200:
                if self.PRINT_OUT:
                    print(f"[+] Connected successfully.")
                return True
            else:
                self.client_socket.close()
                return False
        except Exception as e:
            if self.PRINT_OUT:
                print(f"[^] Connection error: {e}")
            return False

    

    def send_message_raw(self, message) -> bool:
        try:
            # self.client_socket.send(message.encode())
            # response = self.client_socket.recv(4096)
            # return response.decode()
            # self.client_socket.send(json.dumps(message).encode())
            self._send_data(json.dumps(message).encode())
            return True
        except Exception as e:
            if self.PRINT_OUT:
                print(f"[^] Message sending error: {e}")
            return False
    
    def send_message(self, message) -> bool:
        try:
            # self.client_socket.send(message.encode())
            # response = self.client_socket.recv(4096)
            # return response.decode()
            # self.client_socket.send(json.dumps(message).encode())
            data = {
                "type": "message",
                "data": message,
            }
            self._send_data(json.dumps(data).encode())
            return True
        except Exception as e:
            if self.PRINT_OUT:
                print(f"[^] Message sending error: {e}")
            return False
    
    def receive_message(self, auto_keepalive=True) -> dict:
        try:
            while True:
                try:
                    # response = self.client_socket.recv(4096)
                    response = self._recv_data()
                    if not response or response == b"":
                        return None
                    data = response.decode()
                    json_data = json.loads(data)
                    if "type" in json_data:
                        if json_data["type"] == "keepalive":
                            # if "keep" in json_data:
                            #     if json_data["keep"] == True:
                            #         continue
                            if not auto_keepalive:
                                continue
                            self._send_keepalive()
                            continue
                    return json_data
                except Exception:
                    continue
        except Exception as e:
            if self.PRINT_OUT:
                print(f"[^] Message receiving error: {e}")
            return None

    def close(self):
        self.client_socket.close()


