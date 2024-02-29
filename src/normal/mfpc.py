#!/bin/python3
# VERSION CODE
# => 1 / NORMAL
# SUB VERSION CODE
# => 2
import socket
import json
import time
import hashlib
import sys

ARGV = sys.argv
HOST = 'localhost'
PORT = 20035
NOINPUT = False
NORECV = False
RECV_BUF_SIZE = 4096 * 8
in_host = None
in_port = None
in_password = None
if len(ARGV) >= 3:
    in_host = ARGV[1]
    in_port = int(ARGV[2])
    if len(ARGV) == 4:
        in_password = ARGV[3]

def connect_to_server():
    global in_host
    global in_port
    global in_password
    try:
        if not in_host:
            host = input("[?] Host > ")
        else:
            host = in_host
        if not in_port:
            port = int(input("[?] Port > "))
        else:
            port = int(in_port)
        if not in_password:
            password = input("[?] Password > ")
        else:
            password = in_password
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        print(f"[+] Successfully connected to {host}:{port}")

        auth_data = {'auth': get_signature(password)}
        client_socket.send(json.dumps(auth_data).encode())

        response = client_socket.recv(RECV_BUF_SIZE)
        response_data = json.loads(response.decode())
        code = response_data.get('code')
        if code == 200:
            print("[$] Verification passed")
            start_messaging(client_socket)
        else:
            print(f"[$] Validation failed: {response_data.get('data')}")
            client_socket.close()

    except Exception as e:
        print(f"[-] Connect error: {e}")

def get_signature(password):
    timestamp = str(int(time.time()))
    data = timestamp[:8] + password + timestamp[:8]
    hashed_data = hashlib.sha256(data.encode()).hexdigest()
    return hashed_data

def start_messaging(client_socket):
    global NOINPUT, NORECV
    print("[>] You can start sending messages now (enter 'q' to exit, 'w' to enter loop mode, 's' to enter sending mode)")
    try:
        while True:
            if not NOINPUT:
                message = input(">>> ")
                if message == 'q' or message.strip() == 'q':
                    break
                if message == 'w' or message.strip() == 'w':
                    print(f"[~] Loop Mode => True")
                    NORECV = False
                    NOINPUT = True
                    continue
                if message == 's' or message.strip() == 's':
                    print(f"[~] Sending Mode => True")
                    NORECV = True
                    continue
                if message == '' or message.strip() == '':
                    pass 

                client_socket.send(message.encode())
            if not NORECV:
                response = client_socket.recv(RECV_BUF_SIZE).decode()
                if not NOINPUT:
                    print(f"[*] Received messages: {response}")
                else:
                    print(f"[*] Message > {response}")

    except Exception as e:
        print(f"[-] Message sending/receiving error: {e}")

    finally:
        client_socket.close()

connect_to_server()
