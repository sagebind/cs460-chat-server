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
    def __init__(self):
        self.tokens = {}

    """
    Authenticates and logs in a user.
    """
    def login(self, username, password, address):
        # Make sure the user exists.
        if not accounts.manager.user_exists(username):
            raise AuthenticationException("User does not exist")

        # Validate password.
        if not accounts.manager.validate_password(username, password):
            raise AuthenticationException("Invalid password")

        # Generate a new access token.
        token = Token(username, address)
        # Store the token, along with the username and the time it expires.
        self.tokens[token.token] = token

        return token.token

    """
    Logs a user out.
    """
    def logout(self, token):
        del self.tokens[token]

    """
    Get the user for a given token.
    """
    def get_token_user(self, token):
        return self.tokens[token].username

    """
    Get the IP address and port of a client using a token.
    """
    def get_token_address(self, token):
        return self.tokens[token].address

    """
    Validates a given authentication token.
    """
    def validate_token(self, token):
        # Check if token exists.
        if not token in self.tokens:
            raise AuthenticationException("Invalid token")

        # Check if token expired.
        if self.tokens[token].is_expired():
            # Delete expired tokens to cleanup.
            del self.tokens[token]
            raise AuthenticationException("Invalid token")

        # Since the token didn't expire, update the expire time and return success.
        self.tokens[token].update_expires()


"""
Generates a new random authentication token.
"""
class Token:
    lifetime = 900 # 15 minutes

    def __init__(self, username, address):
        # Store info.
        self.username = username
        self.address = address
        self.expires = time.time() + Token.lifetime

        # Generate token string.
        random_bytes = str(uuid.uuid4()).encode()
        time_bytes = int(time.time()).to_bytes(8, byteorder='big')
        self.token = hashlib.sha256(random_bytes + time_bytes).hexdigest()

    def is_expired(self):
        return self.expires <= time.time()

    def update_expires(self):
        self.expires = time.time() + Token.lifetime


manager = SessionManager()
