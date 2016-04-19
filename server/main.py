from server import rpc
from server.modules import (accounts, session)
import logging
import socket
import threading


"""
An RPC server that waits for connections from peers and handles them on
separate threads.
"""
class Server:
    def __init__(self, handler):
        self.handler = handler

    def listen(self, port):
        # Set up a connection server.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("0.0.0.0", port))
        self.socket.listen(1)

        # Loop forever to accept connections.
        while True:
            # Accept the next connection.
            try:
                connection, address = self.socket.accept()
                connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            except KeyboardInterrupt:
                logging.info("Shutting down")
                break

            # Spawn a separate thread to handle the connection.
            logging.info("Received connection from %s", address)
            listener = rpc.Listener(connection, self.handler)
            thread = ServerThread(listener)
            thread.start()


"""
Thread that handles a connection to a client.
"""
class ServerThread(threading.Thread):
    def __init__(self, listener):
        threading.Thread.__init__(self)
        self.listener = listener

    def run(self):
        proxy = rpc.Proxy(self.listener)
        self.listener.join()
        self.listener.close()
        logging.info("Client %s disconnected", proxy.get_peer_name())


"""
Primary handler for client connections.
"""
class Handler:
    def say_hello(self):
        return "Hello"


def main():
    # Set the logging level.
    logging.getLogger().setLevel(logging.DEBUG)

    # Set up the log handler.
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    logging.getLogger().addHandler(handler)

    # Initialize modules.
    accountManager = accounts.AccountManager()
    sessionManager = session.SessionManager()

    server = Server(Handler)
    server.listen(6543)
