'''
    This file will handle our typical Bottle requests and responses 
    You should not have anything beyond basic page loads, handling forms and 
    maybe some simple program logic
'''
import gevent.monkey
gevent.monkey.patch_all()
import bottle
from bottle import route, get, post, error, request, static_file, run
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
import model
from no_sql_db import database
import collections
from time import time
from gevent import sleep
import base64
import os
from cryptography.fernet import Fernet

messages = collections.deque()

MESSAGE_TIMEOUT = 10
FLOOD_MESSAGES = 5
FETCH_FREQ = 1000

class Message(object):
    def __init__(self, nick, text):
        self.time = time()
        self.nick = nick
        self.text = text

    def json(self):
        return {'text': self.text, 'nick': self.nick, 'time': self.time}

js = '''

'''

random_key = Fernet.generate_key()
fernet = Fernet(random_key)


user = ""
chat_members = []
logged_in = []
header = "header"

#-----------------------------------------------------------------------------
# Static file paths
#-----------------------------------------------------------------------------

# Allow image loading
@route('/img/<picture:path>')
def serve_pictures(picture):
    '''
        serve_pictures

        Serves images from static/img/

        :: picture :: A path to the requested picture

        Returns a static file object containing the requested picture
    '''
    return static_file(picture, root='static/img/')

#-----------------------------------------------------------------------------

# Allow CSS
@route('/css/<css:path>')
def serve_css(css):
    '''
        serve_css

        Serves css from static/css/

        :: css :: A path to the requested css

        Returns a static file object containing the requested css
    '''
    return static_file(css, root='static/css/')

#-----------------------------------------------------------------------------

# Allow javascript
@route('/js/<js:path>')
def serve_js(js):
    '''
        serve_js

        Serves js from static/js/

        :: js :: A path to the requested javascript

        Returns a static file object containing the requested javascript
    '''
    return static_file(js, root='static/js/')

#-----------------------------------------------------------------------------
# Pages
#-----------------------------------------------------------------------------

# Redirect to login
@get('/')
@get('/home')
def get_index():
    '''
        get_index
        
        Serves the index page
    '''
    return model.index(user, header)

#-----------------------------------------------------------------------------

# Display the login page
@get('/login')
def get_login_controller():
    '''
        get_login
        
        Serves the login page
    '''
    return model.login_form(header)

#-----------------------------------------------------------------------------


@get('/logout')
def logout():
    global user
    global header
    global messages
    header = "header"
    collections.deque.clear(messages)
    if user in chat_members:
        chat_members.remove(user)
    user = ""
    return model.logout(header)

#-----------------------------------------------------------------------------

#Chat
@get('/chat')
@get('/:channel')
def chat(channel="lobby"):
    return model.chat(user, header, chat_members)


@get('/api/info')
def on_info():
    return {
        'server_name': 'Bottle Test Chat',
        'server_time': time(),
        'refresh_interval': 1000
    }
    
@post('/api/send_message')
def on_message():
    text = request.forms.get('text')
    nick = user
    if not text: return {'error': 'No text.'}

    # Flood protection
    if len([m for m in messages if m.nick == nick]) > FLOOD_MESSAGES:
        return {'error': 'Messages arrive too fast.'}
    text = fernet.encrypt(text.encode())
    messages.append(Message(nick, text))
    return {'status': 'OK'}

@get('/api/fetch')
def on_fetch():
    ''' Return all messages of the last ten seconds. '''
    since = float(request.params.get('since', 0))
    # Fetch new messages
    temp = []
    for m in messages:
        text = fernet.decrypt(m.text).decode()
        message = Message(m.nick, text)
        message.time = m.time
        temp.append(message)
    updates = [m.json() for m in temp if m.time > since]
    # Send up to 10 messages at once.
    return { 'messages': updates[:10] }

#-----------------------------------------------------------------------------

# Attempt the login
@post('/login')
def post_login():
    '''
        post_login
        
        Handles login attempts
        Expects a form containing 'username' and 'password' fields
    '''
    global user
    global header
    global chat_members
    # Handle the form processing
    username = request.forms.get('username')
    password = request.forms.get('password')
    hash = SHA256.new()
    hash.update(password.encode())
    password = hash.hexdigest().encode()
    
    # Call the appropriate method
    if model.login_check(username, password) and (len(chat_members) != 2 or username in chat_members):
        user = username
        header = "loggedinheader"
        friends = [name for name in database.passwords.keys() if name != username]
        if not friends:
            friends = "No friends :("
        if username not in chat_members:
            chat_members.append(username)
        
        return model.page_view("index", name=username, data=friends, header=header)
    else:   
        return model.page_view("invalid", reason="Invalid username or password/User doesn't exist/Too many users logged in.", header=header)



#-----------------------------------------------------------------------------

# Display the register page
@get('/register')
def get_register_controller():

    return model.register(header)

#-----------------------------------------------------------------------------

@post('/register')
def post_register():
    '''
        post_login
        
        Handles login attempts
        Expects a form containing 'username' and 'password' fields
    '''

    # Handle the form processing
    username = request.forms.get('username')
    password = request.forms.get('password')
    password_c = request.forms.get('password_confirm')
    upper = any(c.isupper() for c in password)
    special = any(not c.isalnum() and c != ' ' for c in password)
    num = any(c.isnumeric() for c in password)
    length = len(password)
    hash = SHA256.new()
    hash.update(password.encode())
    password = hash.hexdigest().encode()
    hash = SHA256.new()
    hash.update(password_c.encode())
    password_c = hash.hexdigest().encode()
    
    # Call the appropriate method
    return model.register_check(username, password, password_c, length, upper, num, special, header)


#-----------------------------------------------------------------------------

@get('/about')
def get_about():
    '''
        get_about
        
        Serves the about page
    '''
    return model.about(header)
#-----------------------------------------------------------------------------

# Help with debugging
@post('/debug/<cmd:path>')
def post_debug(cmd):
    return model.debug(cmd)

#-----------------------------------------------------------------------------

# 404 errors, use the same trick for other types of errors
@error(404)
def error(error): 
    return model.handle_errors(error)
