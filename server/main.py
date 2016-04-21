from server import rpc
from server.modules import (accounts, friends, groups, messages, session)
import logging
import socket
import threading


"""
An RPC server that waits for connections from peers and handles them on
separate threads.
"""
class Server:
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
            listener = rpc.Listener(connection)
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
        proxy = rpc.Proxy(self.listener, Handler)
        self.listener.join()
        self.listener.close()
        logging.info("Client %s disconnected", proxy.get_peer_name())


"""
Primary handler for client connections.
"""
class Handler(rpc.Handler):
    def login(self, username, password):
        token = session.manager.login(username, password, self.proxy.get_peer_name())

        # Set up callback handler.
        messages.manager.set_callback(username, lambda message: self.proxy.receive_message(**message))

        return token

    def logout(self, token):
        session.manager.validate_token(token)
        username = session.manager.get_token_user(token)
        messages.manager.remove_callback(username)
        return session.manager.logout(token)

    def get_users(self):
        return accounts.manager.get_users()

    def get_user(self, username):
        user = accounts.manager.get_user(username)
        return {
            "username": user.username,
            "email": user.email
        }

    def create_user(self, username, password, first_name, last_name, email, address):
        accounts.manager.create_user(
            username,
            password,
            first_name,
            last_name,
            email,
            address
        )
        return True

    def delete_user(self, token, username):
        session.manager.validate_token(token)

    def get_messages(self, token, username, group, start_time, end_time):
        session.manager.validate_token(token)

    def send_message(self, token, receiver, text):
        session.manager.validate_token(token)
        sender = session.manager.get_token_user(token)
        messages.manager.send(sender, receiver["type"], text, username=receiver.get("username", None), group=receiver.get("id", None))
        return True

    def get_groups(self, token):
        session.manager.validate_token(token)
        username = session.manager.get_token_user(token)
        return groups.manager.get_groups_with_user(username)

    def get_group(self, token, id):
        session.manager.validate_token(token)

    def create_group(self, token):
        session.manager.validate_token(token)

    def add_group_user(self, token, group, username):
        session.manager.validate_token(token)

    def remove_group_user(self, token, group, username):
        session.manager.validate_token(token)

    def delete_group(self, token, group):
        session.manager.validate_token(token)

    def get_friends(self, token):
        session.manager.validate_token(token)
        username = session.manager.get_token_user(token)
        return friends.manager.get_friends(username)

    def add_friend(self, token, username):
        session.manager.validate_token(token)
        owner_username = session.manager.get_token_user(token)
        friends.manager.add_friend(owner_username, username)
        return True

    def remove_friend(self, token, username):
        session.manager.validate_token(token)
        username = session.manager.get_token_user(token)


def main():
    # Set the logging level.
    logging.getLogger().setLevel(logging.DEBUG)

    # Set up the log handler.
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    logging.getLogger().addHandler(handler)

    server = Server()
    server.listen(6543)
