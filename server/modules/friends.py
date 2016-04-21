from server.modules import accounts
import pickle


class FriendManager:
    def __init__(self):
        try:
            with open('friends.pickle', 'rb') as f:
                self.friends = pickle.load(f)
        except FileNotFoundError:
            self.friends = {}

    """
    Gets a list of friends for a given user.
    """
    def get_friends(self, username):
        accounts.manager.validate_user(username)

        if username in self.friends:
            return self.friends[username]
        # User has no friends. :(
        return []

    """
    Adds a user as a friend for a given user.
    """
    def add_friend(self, username, friend_username):
        accounts.manager.validate_user(username)
        accounts.manager.validate_user(friend_username)

        if not username in self.friends:
            self.friends[username] = [friend_username]
        elif not friend_username in self.friends[username]:
            self.friends[username].append(friend_username)

        self.save()

    def save(self):
        with open('friends.pickle', 'wb') as f:
            pickle.dump(self.friends, f)


manager = FriendManager()
