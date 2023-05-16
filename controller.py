'''
    This file will handle our typical Bottle requests and responses 
    You should not have anything beyond basic page loads, handling forms and 
    maybe some simple program logic
'''
import uuid
import gunicorn
import gevent.monkey
gevent.monkey.patch_all()
from bottle import Bottle, run, install, route, get, post, error, request, static_file, response, redirect, default_app
from Crypto.Hash import SHA256
import model
from no_sql_db import database
import collections
from time import time
import os
import pickle
import httpagentparser
from datetime import datetime
from beaker.middleware import SessionMiddleware

host = '0.0.0.0'
localhost = '127.0.0.1'
port = 8006
debug = True

'''
MULTIPLE LOGIN SESSIONS BY ACCESSING SERVER FROM DIFFERENT BROWSERS (i.e chrome, firefox, safari)
note: all chromium based browsers will be treated as being accesssed from the same browser
'''

MESSAGE_TIMEOUT = 10
FLOOD_MESSAGES = 5

app = Bottle()

session_opts = {
    'session.type': 'cookie',
    'session.cookie_expires': True,
    'session.auto': True,
    'session.key': 'myapp_session',
    'session.validate_key': 'supersecretkey'
}

session_app = SessionMiddleware(app, session_opts)

class Message(object):
    def __init__(self, nick, text):
        self.time = time()
        self.nick = nick
        self.text = text

    def json(self):
        return {'text': self.text, 'nick': self.nick, 'time': self.time}

js = '''

'''

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
messages = collections.deque()
muted = []
header = "header"
documents = []


if os.path.isfile("./documents.pkl"):
    with open("./documents.pkl", "rb") as f:
        documents = pickle.load(f)
#-----------------------------------------------------------------------------
# Static file paths
#-----------------------------------------------------------------------------

# Allow image loading
@app.route('/img/<picture:path>')
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
@app.route('/css/<css:path>')
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
@app.route('/js/<js:path>')
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
#Verify a session
def verify():
    global header
    session = request.environ.get('beaker.session')
    username = ""
    if session is not None and session == request.environ.get('beaker.session'):
        username = session.get('username')
        if username:
            header = "loggedinheader"
        else:
            header = "header"
    return username

# Redirect to login
@app.get('/')
@app.get('/home')
def get_index():
    '''
        get_index
        
        Serves the index page
    '''
    user = verify()
    return model.index(user, header)

#-----------------------------------------------------------------------------

# Display the login page
@app.get('/login')
def get_login_controller():
    '''
        get_login
        
        Serves the login page
    '''
    return model.login_form(header)

#-----------------------------------------------------------------------------

@app.get('/upload')
def upload():
    user = verify()
    return model.upload(user, header)

# Handle POST request to upload a document
@app.post('/upload')
def upload():
    global documents
    document_name = request.forms.get('documentName')
    document_password = request.forms.get('documentPassword')
    document_category = request.forms.get('documentCategory')
    document_file = request.files.get('documentFile')
    if not document_file:
        return {'message': 'No document provided'}
    path = f"./uploads/{document_category}/{document_file.filename}"
    if os.path.isfile(path):
        return {'message': 'Document already exists'}
    for doc in documents:
        if doc.name == document_name and doc.category == document_category:
            return {'message': 'Document already exists'}
    document_file.save(path)
    documents.append(Document(document_name, document_password, verify(), document_category, path, round(os.stat(path).st_size / (1024 * 1024), 2), os.path.splitext(path)[1], datetime.today().strftime('%Y-%m-%d')))
    with open("documents.pkl", "wb") as f:
        pickle.dump(documents, f)
    return {'message': 'Document uploaded successfully'}

@app.get('/lectures')
def lecture():
    return model.lectures()

@app.get('/documents')
def get_filtered_documents():
    search_term = request.query.get('search')
    sort_option = request.query.get('sort')
    password_filter = request.query.get('password')
    
    filtered_documents = documents

    if search_term:
        filtered_documents = [doc for doc in filtered_documents if search_term.lower() in doc.name.lower()]

    if sort_option == 'name':
        filtered_documents = sorted(filtered_documents, key=lambda doc: doc.name)
    elif sort_option == 'date':
        filtered_documents = sorted(filtered_documents, key=lambda doc: datetime.strptime(doc.date, '%Y-%m-%d'), reverse=True)

    if password_filter == 'password':
        filtered_documents = [doc for doc in filtered_documents if doc.password]
    elif password_filter == 'no-password':
        filtered_documents = [doc for doc in filtered_documents if not doc.password]

    return {'documents': [doc.__dict__ for doc in filtered_documents]}

@app.post('/download')
def download_document():
    document_path = request.forms.get('document_path')
    password = request.forms.get('password')
    document = next((doc for doc in documents if doc.path == document_path), None)
    if document and password == document.password:
        file_name = os.path.basename(document.path)
        response.headers['Content-Disposition'] = f'attachment; filename={file_name}'
        return static_file(file_name, root=os.path.dirname(document.path), download=True)
    else:
        response.status = 401

@app.get('/tutorials')
def tutorial():
    return model.tutorials()

@app.get('/assignments')
def assignment():
    return model.tutorials()

@app.get('/other')
def other():
    return model.tutorials()

@app.get('/logout')
def logout():
    global header
    session = request.environ.get('beaker.session')
    
    if 'session_id' in session:
        session.delete()
        header = "header"
    return redirect('/login')

@app.get('/delete')
def delete():
    user = verify()
    return model.delete(user, header)

@app.post('/delete')
def delete_post():
    # Handle the form processing
    username = request.forms.get('username')
    filename = request.forms.get('filename')
    category = request.forms.get('documentCategory')
    mute = request.forms.get('mute')
    clear = request.forms.get('clear')
    if clear:
        if clear == "CONFIRM":
            #Clear chat history on logout
            collections.deque.clear(messages)
            return model.page_view("delete", header=header, reason="Successfully cleared chat!")
        else:
            return model.page_view("delete", header=header, reason="Wrong phrase to clear chat!")
    if username:
        if not database.delete_user(username):
            return model.page_view("delete", header=header, reason="Failed to delete user (May not exist)")
        return model.page_view("delete", header=header, reason=f"Successfully deleted {username}!")
    if mute:
        if mute in database.passwords.keys():
            if mute != "admin":
                muted.append(mute)
                return model.page_view("delete", header=header, reason=f"Successfully muted {mute}!")
            else:
                return model.page_view("delete", header=header, reason="Failed to mute user (May not exist)")
    if filename:
        if not category:
            return model.page_view("delete", header=header, reason="Specify a category when deleting a file")
        global documents
        for doc in documents:
            if doc.name == filename and doc.category == category:
                documents.remove(doc)
                os.remove(doc.path)
                with open("documents.pkl", "wb") as f:
                    pickle.dump(documents, f)
            return model.page_view("delete", header=header, reason=f"Deleted {filename} in {category}.")
        return model.page_view("delete", header=header, reason="File does not exit")
    return model.page_view("delete", header=header, reason="")

#-----------------------------------------------------------------------------
#Chat
@app.get('/chat')
@app.get('/:channel')
def chat(channel="lobby"):
    user = verify()
    return model.chat(user, header)

'''
All functions here called from javascript for messaging features
'''
@app.get('/api/info')
def on_info():
    return {
        'server_name': 'Bottle Test Chat',
        'server_time': time(),
        'refresh_interval': 1000
    }

@app.post('/api/send_message')
def on_message():
    text = request.forms.get('text')
    nick = verify()
    if not text: return {'error': 'No text.'}

    # Flood protection
    if len([m for m in messages if m.nick == nick]) > FLOOD_MESSAGES:
        return {'error': 'Messages arrive too fast.'}
    if nick not in muted:
        messages.append(Message(nick, text))
    return {'status': 'OK'}

@app.get('/api/fetch')
def on_fetch():
    ''' Return all messages '''
    # Fetch new messages
    updates = [m.json() for m in messages]
    return { 'messages': updates }

#-----------------------------------------------------------------------------

# Attempt the login
@app.post('/login')
def post_login():
    '''
        post_login
        
        Handles login attempts
        Expects a form containing 'username' and 'password' fields
    '''
    global header
    # Handle the form processing
    username = request.forms.get('username')
    password = request.forms.get('password')
    hash = SHA256.new()
    hash.update(password.encode())
    password = hash.hexdigest().encode()
    # Call the appropriate method
    if model.login_check(username, password):
        session = request.environ.get('beaker.session')
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        session['username'] = username
        session.save()
        return redirect('/home')
    else:   
        return model.page_view("reason", reason="Invalid username or password/User doesn't exist", header=header)



#-----------------------------------------------------------------------------

# Display the register page
@app.get('/register')
def get_register_controller():
    user = verify()
    return model.register(header)

#-----------------------------------------------------------------------------

@app.post('/register')
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

# Help with debugging
@app.post('/debug/<cmd:path>')
def post_debug(cmd):
    return model.debug(cmd)

#-----------------------------------------------------------------------------

# 404 errors, use the same trick for other types of errors
@app.error(404)
def error(error): 
    return model.handle_errors(error)

# Run the application
if __name__ == '__main__':
    run(app=session_app, host=host, port=port, debug=debug, server='gunicorn', certfile='./certs/info2222.project.crt', keyfile='./certs/info2222.project.key')