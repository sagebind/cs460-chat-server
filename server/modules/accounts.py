import hashlib
import pickle


class AccountManager:
    def __init__(self):
        try:
            with open('accounts.pickle', 'rb') as f:
                self.accounts = pickle.load(f)
        except FileNotFoundError:
            self.accounts = {}

    def user_exists(self, username):
        return username in self.accounts

    def get_users(self):
        return list(map(lambda user: user.username, self.accounts.values()))

    def get_user(self, username):
        if not self.user_exists(username):
            raise Exception("No such user exists.")
        return self.accounts[username]

    def validate_password(self, username, password):
        if not self.user_exists(username):
            return False

        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        if self.get_user(username).password != encrypted_password:
            return False

        return True

    def create_user(self, username, password, first_name, last_name, email, address):
        if self.user_exists(username):
            raise Exception("A user with that username already exists!")

        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        account = Account(username, encrypted_password, first_name, last_name, email, address)
        self.accounts[username] = account

        self.save()

    def delete_user(self, username):
        if self.user_exists(username):
            del self.accounts[username]
            self.save()

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
