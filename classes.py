import time
class Message(object):
    def __init__(self, nick, text):
        self.time = time()
        self.nick = nick
        self.text = text

    def json(self):
        return {'text': self.text, 'nick': self.nick, 'time': self.time}
    
class Document(object):
    def __init__(self, name, password, owner, category, path, size, filetype, date):
        self.path = path
        self.password = password
        self.name = name
        self.owner = owner
        self.category = category
        self.size = size
        self.filetype = filetype
        self.date = date
        