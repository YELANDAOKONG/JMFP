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
import sys

ARGV = sys.argv
MAX_PACKET_SIZE = 1024 * 1024
SOCKET_TIMEOUT = 60
HOST = 'localhost'
PORT = 20035
NOINPUT = False
NORECV = False

in_host = None
in_port = None
in_password = None
if len(ARGV) >= 3:
    in_host = ARGV[1]
    in_port = int(ARGV[2])
    if len(ARGV) == 4:
        in_password = ARGV[3]

def get_signature(password):
    timestamp = str(int(time.time()))
    data = timestamp[:8] + password + timestamp[:8]
    hashed_data = hashlib.sha256(data.encode()).hexdigest()
    return hashed_data

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

def client_recv(socket) -> bytes:
    try:
        # socket.settimeout(SOCKET_TIMEOUT)
        header = socket.recv(4)
        data_length = int.from_bytes(header, byteorder='big')
        # if data_length > MAX_PACKET_SIZE:
        #     socket.close()
        #     return b""
        data = socket.recv(data_length)
        return data
    except socket.timeout as se:
        # print(f"[^] The server timed out. Closing the connection.")
        return b""
    except Exception as e:
        # print(f"[^] An error occurred while handling the server: {e}") y
        return b""
    finally:
        # socket.close()
        pass

def send_keepalive(client_socket) -> bool:
    keepalive_data = {
        "type": "keepalive",
        "keep": True
    }
    return client_send(client_socket, json.dumps(keepalive_data).encode())

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
        client_socket.settimeout(SOCKET_TIMEOUT)
        client_socket.connect((host, port))
        print(f"[+] Successfully connected to {host}:{port}")

        auth_data = {'auth': get_signature(password)}
        # client_socket.send(json.dumps(auth_data).encode())
        result = client_send(client_socket, json.dumps(auth_data).encode())
        if not result:
            print("[!] Verification message failed to send")
            return

        # response = client_socket.recv(4096)
        response = client_recv(client_socket)
        if not response or response == b"":
            print("[!] Verification message failed to receive")
            return
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

def start_messaging(client_socket):
    global NOINPUT, NORECV
    print("[>] You can start sending messages now (enter 'q' to exit, 'w' to enter loop mode, 's' to enter sending mode)")
    try:
        while True:
            noeverything = False
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
                    NORECV = not NORECV
                    print(f"[~] Sending Mode => {NORECV}")
                    continue
                if message == '' or message.strip() == '':
                    noeverything = True
                    # continue
                    pass 

                # client_socket.send(message.encode())
                if not noeverything:
                    try:
                        data_dict = json.loads(message)
                        # client_socket.send(json.dumps(data_dict).encode())
                        client_send(client_socket, json.dumps(data_dict).encode())
                    except json.JSONDecodeError as je:
                        print(f"[#] Client > Invalid JSON Format")
            if not NORECV:
                # response = client_socket.recv(4096).decode()
                response_source = client_recv(client_socket)
                if not response_source or response_source == b'':
                    print(f"[^] No response from server")
                    continue
                response = response_source.decode()
                try:
                    response_dict = json.loads(response)
                    if not NOINPUT:
                        print(f"[*] Received messages: {response}")
                    else:
                        print(f"[*] Message > {response}")
                    if "type" in response_dict and response_dict["type"] == "keepalive":
                        # if "keep" in response_dict and response_dict["keep"] == True:
                        #     send_keepalive(client_socket)
                        send_keepalive(client_socket)
                        print("[&] Sent keepalive packet")
                except json.JSONDecodeError as je:
                    print(f"[^] Message > Invalid JSON Format")
                    continue

    except Exception as e:
        print(f"[-] Message sending/receiving error: {e}")
    finally:
        client_socket.close()
        pass

connect_to_server()
