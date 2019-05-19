#!/usr/bin/env python3

import socket
import threading
import socketserver
import time

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        cur_thread_name = threading.current_thread().name

        while True:
            data = str(self.request.recv(1024), 'ascii')
            print("Thread {}: got {} bytes.".format(cur_thread_name, len(data)))
            if len(data) == 0:
                print('Empty message received; quit handler.')
                break
            response = bytes("{}: {}".format(cur_thread_name, data), 'ascii')
            self.request.sendall(response)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def client(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        count = 0
        while count < 10:
            count += 1
            print("Sending: {}".format(message))
            sock.sendall(bytes(message, 'ascii'))
            response = str(sock.recv(1024), 'ascii')
            print("Received: {}".format(response))
            time.sleep(2)

if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 7778

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address
    print("ip: {}; port: {}".format(ip, port))
    with server:
        try:
            # Start a thread with the server -- that thread will then start one
            # more thread for each request
            server_thread = threading.Thread(target=server.serve_forever)
            # Exit the server thread when the main thread terminates
            server_thread.daemon = True
            server_thread.start()
            print("Server loop running in thread:", server_thread.name)

            # client(ip, port, "Hello World 1")
            # client(ip, port, "Hello World 2")
            # client(ip, port, "Hello World 3")
            response = "keep going"
            while response.lower().find("quit") < 0:
                response = input('Type "quit" to terminate server: ')
            
        finally:
            print('Server close')
            server.server_close()
            print('Server shutdown')
            server.shutdown()
