import hashlib
import pickle


"""
Manages the list of accounts.
"""
class AccountManager:
    def __init__(self):
        try:
            with open('accounts.pickle', 'rb') as f:
                self.accounts = pickle.load(f)
        except FileNotFoundError:
            self.accounts = {}

    """
    Checks if a user exists.
    """
    def user_exists(self, username):
        return username in self.accounts

    """
    Validates a given username.
    """
    def validate_user(self, username):
        if not username in self.accounts:
            raise Exception("User " + username + " does not exist")

    """
    Gets a list of all users.
    """
    def get_users(self):
        return list(self.accounts.keys())

    """
    Gets information about a user by their username.
    """
    def get_user(self, username):
        self.validate_user(username)
        return self.accounts[username]

    """
    Creates a new user.
    """
    def create_user(self, username, password, first_name, last_name, email, address):
        if self.user_exists(username):
            raise Exception("A user with that username already exists!")

        if len(password) < 6:
            raise Exception("Password must be at least 6 characters")

        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        account = Account(username, encrypted_password, first_name, last_name, email, address)
        self.accounts[username] = account

        self.save()

    """
    Deletes a user.
    """
    def delete_user(self, username):
        self.validate_user(username)
        if self.user_exists(username):
            del self.accounts[username]
            self.save()

    """
    Validates a user's password.
    """
    def validate_password(self, username, password):
        if not self.user_exists(username):
            return False

        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        if self.get_user(username).password != encrypted_password:
            return False

        return True

    """
    Save the list of accounts.
    """
    def save(self):
        with open('accounts.pickle', 'wb') as f:
            pickle.dump(self.accounts, f)


class Account:
    def __init__(self, username, password, first_name, last_name, email, address):
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.address = address
        self.online = False


manager = AccountManager()
