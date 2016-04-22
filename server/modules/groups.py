from server.modules import accounts
import pickle
import uuid


"""
Manages groups.
"""
class GroupManager:
    def __init__(self):
        try:
            with open('groups.pickle', 'rb') as f:
                (self.groups, self.user_map) = pickle.load(f)
        except FileNotFoundError:
            self.groups = {}
            self.user_map = {}

    """
    Checks if a group exists.
    """
    def group_exists(self, id):
        return id in self.groups

    """
    Validates a group ID.
    """
    def validate_group(self, id):
        if not id in self.groups:
            raise Exception("Group does not exist")

    """
    Gets a list of all groups.
    """
    def get_groups(self):
        return list(self.groups.keys())

    """
    Gets a list of groups that contain a given user.
    """
    def get_groups_with_user(self, username):
        accounts.manager.validate_user(username)

        if not username in self.user_map:
            return []

        return self.user_map[username]

    """
    Gets details about a group.
    """
    def get_group(self, id):
        self.validate_group(id)

        group = self.groups[id]
        group["name"] = ", ".join(group["users"])
        return group

    """
    Creates a new group and returns its ID.
    """
    def create_group(self):
        id = str(uuid.uuid4())
        self.groups[id] = {
            "id": id,
            "users": []
        }

        self.save()
        return id

    """
    Deletes a group.
    """
    def delete_group(self, id):
        self.validate_group(id)

        for username in self.groups[id]["users"]:
            self.user_map[username].remove(id)
        del self.groups[id]

        self.save()

    """
    Adds a user to a group.
    """
    def add_user_to_group(self, username, id):
        accounts.manager.validate_user(username)
        self.validate_group(id)

        self.groups[id]["users"].append(username)

        if username in self.user_map:
            self.user_map[username].append(id)
        else:
            self.user_map[username] = [id]

        self.save()

    """
    Removes a user from a group.
    """
    def remove_user_from_group(self, username, id):
        self.validate_group(id)

        self.groups[id]["users"].remove(username)
        self.user_map[username].remove(id)

        self.save()

    """
    Saves the groups list.
    """
    def save(self):
        with open('groups.pickle', 'wb') as f:
            pickle.dump((self.groups, self.user_map), f)


manager = GroupManager()
