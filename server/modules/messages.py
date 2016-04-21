from server.modules import (accounts, groups)
import pickle
import time


class MessageManager:
    def __init__(self):
        self.callbacks = {}
        try:
            with open('messages.pickle', 'rb') as f:
                self.messages = pickle.load(f)
        except FileNotFoundError:
            self.messages = []

    """
    Sends a message.
    """
    def send(self, sender, receiver_type, text, username=None, group=None):
        message = {
            "id": len(self.messages),
            "sender": sender,
            "receiver": {
                "type": receiver_type
            },
            "timestamp": time.time(),
            "text": text
        }

        if receiver_type == "user":
            accounts.manager.validate_user(username)
            message["receiver"]["username"] = username
        elif receiver_type == "group":
            if not groups.manager.group_exists(group):
                raise Exception("Group does not exist")
            message["receiver"]["id"] = group
        else:
            raise Exception("Invalid recipient type")

        self.messages.append(message)

        # If a callback was set to send a message immediately, invoke it now.
        self.call_callback(sender, message)
        if receiver_type == "user":
            self.call_callback(username, message)
        elif receiver_type == "group":
            for user in groups.manager.get_group(group)["users"]:
                self.call_callback(user, message)

        self.save()

    """
    Sets a callback to be invoked when a given user gets a message.
    """
    def set_callback(self, username, callback):
        self.callbacks[username] = callback

    """
    Removes a callback.
    """
    def remove_callback(self, username):
        del self.callbacks[username]

    """
    Invokes a message callback.
    """
    def call_callback(self, username, message):
        try:
            if username in self.callbacks:
                return self.callbacks[username](message)
        except:
            pass

    def save(self):
        with open('messages.pickle', 'wb') as f:
            pickle.dump(self.messages, f)


manager = MessageManager()
