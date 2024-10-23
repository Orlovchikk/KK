class Database:
    def __init__(self):
        self.users = []

    def check_access(self, username):
        return username in self.users
    
    def add_user(self, username, token):
        if token == '1':
            self.users.append(username)

