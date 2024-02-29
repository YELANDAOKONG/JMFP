#!/bin/python3
# VERSION CODE
# => 1 / NORMAL
# SUB VERSION CODE
# => 2
import socket
import threading
import json
import select
import hashlib
import time

HOST = '0.0.0.0'
PORT = 20035
PASSWORD = 'passwd'
MAX_JSON_SIZE = 1024 * 1024
KEEP_ALIVE_INTERVAL = 10
RECV_BUF_SIZE = 4096 * 8

verified_clients = []
lock = threading.Lock()

def verify_signature(timestamp, password, signature):
    data = timestamp[:8] + password + timestamp[:8]
    hashed_data = hashlib.sha256(data.encode()).hexdigest()
    return hashed_data == signature

def handle_client(client_socket, address):
    try:
        auth_message = client_socket.recv(RECV_BUF_SIZE).decode()
        auth_data = json.loads(auth_message)
        signature = auth_data.get('auth')

        current_timestamp = str(int(time.time()))
        if not verify_signature(current_timestamp, PASSWORD, signature):
            send_response(client_socket, 403, 'Invalid signature', keep=False)
            client_socket.close()
            return

        send_response(client_socket, 200, 'OK', keep=True)

        with lock:
            verified_clients.append(client_socket)

        while True:
            message = client_socket.recv(RECV_BUF_SIZE).decode()
            if not message:
                break

            if len(message) > MAX_JSON_SIZE:
                send_response(client_socket, 400, 'Message too large', keep=False)
                client_socket.close()
                break

            try:
                message_data = json.loads(message)
                forward_data = {
                    "time": int(time.time() * 1000),
                    "addr": address,
                    "data": message_data
                }
                # forward_message(message, address)
                forward_message(json.dumps(forward_data), address)
            except json.JSONDecodeError:
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

def send_response(client_socket, code, data, keep=False):
    response = {'code': code, 'data': data, 'keep': keep}
    _, writable, _ = select.select([], [client_socket], [], 1)
    if client_socket not in writable:
        return
    client_socket.send(json.dumps(response).encode())

def forward_message(message, source_address):
    with lock:
        for client_socket in verified_clients:
            if client_socket.getpeername() != source_address:
                _, writable, _ = select.select([], [client_socket], [], 1)
                if client_socket not in writable:
                    continue
                client_socket.send(message.encode())

def keep_alive_thread():
    while True:
        time.sleep(KEEP_ALIVE_INTERVAL)
        with lock:
            for client_socket in verified_clients:
                _, writable, _ = select.select([], [client_socket], [], 1)
                if client_socket not in writable:
                    continue
                client_socket.send(json.dumps({'keep': True}).encode())

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f'[+] Server listening on {HOST}:{PORT}')

    threading.Thread(target=keep_alive_thread, daemon=True).start()

    try:
        while True:
            client_socket, address = server_socket.accept()
            client_socket.setblocking(True)
            print(f'[%] New connection from {address[0]}:{address[1]}')

            threading.Thread(target=handle_client, args=(client_socket, address)).start()

    except KeyboardInterrupt:
        print('[-] Server stopped')

    finally:
        server_socket.close()

start_server()
