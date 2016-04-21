from server.modules import accounts
import uuid


class GroupManager:
    def __init__(self):
        self.groups = {}
        self.user_map = {}

    def group_exists(self, id):
        return id in self.groups

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

    def get_group(self, group):
        return self.groups[group]

    def create_group(self):
        id = uuid.uuid4()
        self.groups[id] = {
            "id": id,
            "users": []
        }
        return id

    def delete_group(self, group):
        for username in self.groups[group]["users"]:
            self.user_map[username].remove(group)
        del self.groups[group]

    def add_user_to_group(self, username, group):
        accounts.manager.validate_user(username)

        self.groups[group]["users"].append(username)

        if username in self.user_map:
            self.user_map[username].append(group)
        else:
            self.user_map[username] = [group]

    def remove_user_from_group(self, username, group):
        self.groups[group]["users"].remove(username)
        self.user_map[username].remove(group)


manager = GroupManager()
