from server.modules import accounts
import hashlib
import time
import uuid


class AuthenticationException(Exception):
    pass


"""
Manages login sessions and user authentication.
"""
class SessionManager:
    token_lifetime = 900 # 15 minutes

    def __init__(self):
        self.tokens = {}

    """
    Authenticates and logs in a user.
    """
    def login(self, username, password):
        # Make sure the user exists.
        if not accounts.manager.user_exists(username):
            raise AuthenticationException("User does not exist")

        # Validate password.
        if not accounts.manager.validate_password(username, password):
            raise AuthenticationException("Invalid password")

        # Generate a new access token.
        token = self.generate_token()
        # Store the token, along with the username and the time it expires.
        self.tokens[token] = (username, time.time() + SessionManager.token_lifetime)

        return token

    """
    Logs a user out.
    """
    def logout(self, token):
        del self.tokens[token]

    """
    Validates a given authentication token.
    """
    def validate_token(self, token):
        # Check if token exists.
        if not token in self.tokens:
            raise AuthenticationException("Invalid token")

        # Check if token expired.
        if self.tokens[token][1] <= time.time():
            # Delete expired tokens to cleanup.
            del self.tokens[token]
            raise AuthenticationException("Invalid token")

        # Since the token didn't expire, update the expire time and return success.
        self.tokens[token] = (self.tokens[token][0], time.time() + SessionManager.token_lifetime)

    """
    Generates a new random authentication token.
    """
    def generate_token(self):
        random_bytes = str(uuid.uuid4()).encode()
        time_bytes = int(time.time()).to_bytes(8, byteorder='big')

        token = hashlib.sha256(random_bytes + time_bytes).hexdigest()
        return token


manager = SessionManager()
