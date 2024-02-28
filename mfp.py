#!/bin/python3
# VERSION CODE
# => 2
VERSION_CODE = 2
import socket
import select
import threading
import json
import hashlib
import time
import os
import sys

ARGV = sys.argv
# =======================================================================
# USER CONFIG AREA
# =======================================================================
HOST = '0.0.0.0'
PORT = 20035
PASSWORD = 'passwd'
# =======================================================================
MAX_JSON_SIZE = 1024 * 1024
MAX_PACKET_SIZE = 1024 * 1024 * 1024
KEEP_ALIVE_INTERVAL = 10
SOCKET_TIMEOUT = 60
FORWARD_SYSTEM_MESSAGES = True
verified_clients = []
lock = threading.Lock()

def verify_signature(timestamp, password, signature):
    data = timestamp[:8] + password + timestamp[:8]
    hashed_data = hashlib.sha256(data.encode()).hexdigest()
    return hashed_data == signature

def is_socket_closed(client_socket):
    fileno = client_socket.fileno()
    readable, _, _ = select.select([client_socket], [], [], 0)
    return fileno not in [sock.fileno() for sock in readable]

def client_send(client_socket, data: bytes) -> bool:
    try:
        data_length = len(data)
        header = data_length.to_bytes(4, byteorder='big')
        client_socket.send(header)
        client_socket.send(data)
        return True
    except Exception as e:
        # print(f"[^] Error sending data: {e}")
        return False

def client_recv(client_socket, address: tuple) -> bytes:
    try:
        # client_socket.settimeout(SOCKET_TIMEOUT)
        header = client_socket.recv(4)
        data_length = int.from_bytes(header, byteorder='big')
        # if data_length > MAX_PACKET_SIZE:
        #     send_response(client_socket, 400, "Packet size exceeds the limit.", keep=False)
        #     client_socket.close()
        #     return b""
        data = client_socket.recv(data_length)
        return data
    except socket.timeout as se:
        # print(f"[^] The client {address} timed out. Closing the connection.") 
        return b""
    except Exception as e:
        # print(f"[^] An error occurred while handling the client {address}: {e}") 
        return b""
    finally:
        # client_socket.close()
        pass

def handle_client(client_socket, address: tuple):
    try:
        client_socket.settimeout(SOCKET_TIMEOUT)
        # header = client_socket.recv(4)
        # data_length = int.from_bytes(header, byteorder='big')
        # data = client_socket.recv(data_length).decode()
        # #auth_message = client_socket.recv(4096).decode()
        data = client_recv(client_socket, address)
        if not data or data == b"":
            if not is_socket_closed(client_socket):
                client_socket.close()
            return
        auth_message = data.decode()
        auth_data = json.loads(auth_message)
        signature = auth_data.get('auth')

        current_timestamp = str(int(time.time()))
        if not verify_signature(current_timestamp, PASSWORD, signature):
            send_response(client_socket, 403, 'Invalid signature', keep=False)
            client_socket.close()
            return
        result = send_response(client_socket, 200, 'OK', keep=True)
        if not result:
            client_socket.close()
            return
        with lock:
            verified_clients.append(client_socket)
        if FORWARD_SYSTEM_MESSAGES:
            system_data = {
                "type": "system",
                "event": "client",
                "data": {
                    "type": "connection",
                    "address": address,
                }
            }
            forward_message(
                json.dumps(system_data),
                ("0.0.0.0", 0),
                system_message=True
            )

        while True:
            # message = client_socket.recv(4096).decode()
            message = client_recv(client_socket, address)
            if not message or message == b'':
                break

            if len(message) > MAX_JSON_SIZE:
                send_response(client_socket, 400, 'Message too large', keep=False)
                client_socket.close()
                break

            try:
                message_data = json.loads(message)
                if "type" in message_data and message_data["type"] == "keepalive":
                    # if "keep" in message_data and message_data["keep"] == True:
                    #     continue
                    continue
                if not "data" in message_data:
                    continue
                forward_data = {
                    "type": "message",
                    "time": int(time.time() * 1000),
                    "addr": address,
                    "data": message_data["data"]
                }
                # forward_message(message, address)
                forward_message(json.dumps(forward_data), address)
            except json.JSONDecodeError as jes:
                send_response(client_socket, 400, 'Invalid JSON format', keep=False)
                client_socket.close()
                break

    except Exception as e:
        # print(f'[^] Error handling client: {e}')
        pass

    finally:
        with lock:
            try:
                verified_clients.remove(client_socket)
            except ValueError:
                pass
        client_socket.close()

def send_response(client_socket, code:int, data, keep=False) -> bool:
    response = {
        'type': 'response',
        'code': code,
        'data': data,
        'keep': keep
    }
    # client_socket.send(json.dumps(response).encode())
    return client_send(client_socket, json.dumps(response).encode())

def forward_message(message:str, source_address: tuple, system_message=False):
    with lock:
        for client_socket in verified_clients:
            if (client_socket.getpeername() != source_address) or system_message:
                # client_socket.send(message.encode())
                client_send(client_socket, message.encode())

def keep_alive_thread():
    while True:
        time.sleep(KEEP_ALIVE_INTERVAL)
        with lock:
            for client_socket in verified_clients:
                # client_socket.send(json.dumps({'keep': True}).encode())
                client_send(client_socket, json.dumps({'type':'keepalive' ,'keep': True}).encode())

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f'[+] Server listening on {HOST}:{PORT}')

    threading.Thread(target=keep_alive_thread, daemon=True).start()

    try:
        while True:
            client_socket, address = server_socket.accept()
            print(f'[%] New connection from {address[0]}:{address[1]}')

            threading.Thread(target=handle_client, args=(client_socket, address)).start()

    except KeyboardInterrupt:
        print('[-] Server stopped')

    finally:
        server_socket.close()

start_server()
