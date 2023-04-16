'''
    This file will handle our typical Bottle requests and responses 
    You should not have anything beyond basic page loads, handling forms and 
    maybe some simple program logic
'''
import gevent.monkey
gevent.monkey.patch_all()
from bottle import route, get, post, error, request, static_file
from Crypto.Hash import SHA256
import model
from no_sql_db import database
import collections
from time import time
import httpagentparser

'''
MULTIPLE LOGIN SESSIONS BY ACCESSING SERVER FROM DIFFERENT BROWSERS (i.e chrome, firefox, safari)
note: all chromium based browsers will be treated as being accesssed from the same browser
'''

messages = collections.deque()

MESSAGE_TIMEOUT = 10
FLOOD_MESSAGES = 5

class Message(object):
    def __init__(self, nick, text):
        self.time = time()
        self.nick = nick
        self.text = text

    def json(self):
        return {'text': self.text, 'nick': self.nick, 'time': self.time}

js = '''

'''


user = ""
users = []
browsers = []
header = "header"

#Browser detection for simultaneous logins from different browsers
def detectBrowser():
    agent = request.environ.get('HTTP_USER_AGENT')
    browser = httpagentparser.detect(agent)
    if not browser:
        browser = agent.split('/')[0]
    else:
        browser = browser['browser']['name']  

    return browser

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
    global browsers
    global users
    global user
    global header
    #Check for access from different browser
    browser = detectBrowser()
    if browser not in browsers:
        browsers.append(browser)
        users.append("")
    #Get corresponding user from browser
    user = users[browsers.index(browser)]
    if not user:
        header = "header"
    else:
        header = "loggedinheader"
    return model.index(user, header)

#-----------------------------------------------------------------------------

# Display the login page
@get('/login')
def get_login_controller():
    '''
        get_login
        
        Serves the login page
    '''
    global header
    global user
    browser = detectBrowser()
    if browser not in browsers:
        return get_index()
    user = users[browsers.index(browser)]
    if user:
        header = "loggedinheader"
    else:
        header = "header"
    return model.login_form(header)

#-----------------------------------------------------------------------------


@get('/logout')
def logout():
    global user
    global header
    global messages
    global users
    browser = detectBrowser()
    if browser not in browsers:
        return get_index()
    #Clear chat history on logout
    collections.deque.clear(messages)
    users[browsers.index(browser)] = ""
    user = ""
    header = "header"
    return model.logout(header)

#-----------------------------------------------------------------------------
#Chat
@get('/chat')
@get('/:channel')
def chat(channel="lobby"):
    global user
    global header
    browser = detectBrowser()
    if browser not in browsers:
        return get_index()
    user = users[browsers.index(browser)]
    if user:
        header = "loggedinheader"
    else:
        header = "header"
    return model.chat(user, header)

'''
All functions here called from javascript for messaging features
'''
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
    browser = detectBrowser()
    nick = users[browsers.index(browser)]
    if not text: return {'error': 'No text.'}

    # Flood protection
    if len([m for m in messages if m.nick == nick]) > FLOOD_MESSAGES:
        return {'error': 'Messages arrive too fast.'}
    messages.append(Message(nick, text))
    return {'status': 'OK'}

@get('/api/fetch')
def on_fetch():
    ''' Return all messages '''
    # Fetch new messages
    updates = [m.json() for m in messages]
    return { 'messages': updates }

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
    global users
    global header
    # Handle the form processing
    username = request.forms.get('username')
    password = request.forms.get('password')
    hash = SHA256.new()
    hash.update(password.encode())
    password = hash.hexdigest().encode()
    browser = detectBrowser()
    # Call the appropriate method
    if model.login_check(username, password):
        user = username
        header = "loggedinheader"
        friends = [name for name in database.passwords.keys() if name != username]
        if not friends:
            friends = "No friends :("
        users[browsers.index(browser)] = username
        return model.page_view("index", name=username, data=friends, header=header)
    else:   
        return model.page_view("invalid", reason="Invalid username or password/User doesn't exist", header=header)



#-----------------------------------------------------------------------------

# Display the register page
@get('/register')
def get_register_controller():
    global header
    global user
    browser = detectBrowser()
    if browser not in browsers:
        return get_index()
    user = users[browsers.index(browser)]
    if user:
        header = "loggedinheader"
    else:
        header = "header"
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
    global header
    global user
    browser = detectBrowser()
    if browser not in browsers:
        return get_index()
    user = users[browsers.index(browser)]
    if user:
        header = "loggedinheader"
    else:
        header = "header"
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
