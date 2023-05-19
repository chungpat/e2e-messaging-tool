'''
    This file will handle our typical Bottle requests and responses 
    You should not have anything beyond basic page loads, handling forms and 
    maybe some simple program logic
'''
import uuid
import gunicorn
import gevent.monkey
gevent.monkey.patch_all()
from bottle import Bottle, run, request, static_file, response, redirect
from Crypto.Hash import SHA256
import model
from no_sql_db import database
import collections
from time import time
import os
import pickle
import secrets
from datetime import datetime
from beaker.middleware import SessionMiddleware
from classes import Message, Document

host = '0.0.0.0'
localhost = '127.0.0.1'
port = 8008
debug = True

js = '''

'''
app = Bottle()
validate_key = secrets.token_hex(16) 
session_opts = {
    'session.type': 'cookie',
    'session.cookie_expires': True,
    'session.auto': True,
    'session.key': 'myapp_session',
    'session.validate_key': validate_key
}

session_app = SessionMiddleware(app, session_opts)


messages = collections.deque()
muted = []
header = "header"
documents = []

#Loading documents/resources
if os.path.isfile("./data/documents.pkl"):
    with open("./data/documents.pkl", "rb") as f:
        documents = pickle.load(f)
        
#Loading muted users
if os.path.isfile("./data/muted.pkl"):
    with open("./data/muted.pkl", "rb") as f:
        muted = pickle.load(f)
        
#Loading chat
if os.path.isfile("./data/chat.pkl"):
    with open("./data/chat.pkl", "rb") as f:
        messages = pickle.load(f)

#Function to manage user sessions
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

#Home Page
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
# Logins
#-----------------------------------------------------------------------------
@app.get('/login')
def get_login_controller():
    '''
        get_login
        
        Serves the login page
    '''
    return model.login_form(header)

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
        return model.page_view("/account/login", error_msg="Invalid username or password.", header=header)
    
@app.get('/logout')
def logout():
    global header
    session = request.environ.get('beaker.session')
    
    if 'session_id' in session:
        session.delete()
        header = "header"
    return redirect('/login')

#-----------------------------------------------------------------------------
# Register
#-----------------------------------------------------------------------------
@app.get('/register')
def get_register_controller():
    user = verify()
    return model.register(header)

@app.post('/register')
def post_register():
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
    
    return model.register_check(username, password, password_c, length, upper, num, special, header)

#-----------------------------------------------------------------------------
# Upload feature
#-----------------------------------------------------------------------------

@app.get('/upload')
def upload():
    user = verify()
    return model.upload(user, header)

@app.post('/upload')
def upload():
    global documents
    document_name = request.forms.get('documentName')
    document_password = request.forms.get('documentPassword')
    document_category = request.forms.get('documentCategory')
    document_file = request.files.get('documentFile')
    user = verify()
    if user in muted:
        return {'message': 'You are not able to upload a file. Please contact an admin.'}
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
    with open("./data/documents.pkl", "wb") as f:
        pickle.dump(documents, f)
    return {'message': 'Document uploaded successfully'}

#-----------------------------------------------------------------------------
# Document features (download and filter/sort)
#-----------------------------------------------------------------------------

@app.get('/documents')
def get_filtered_documents():
    search_term = request.query.get('search')
    sort_option = request.query.get('sort')
    password_filter = request.query.get('password')
    category = request.query.get('category')
    
    filtered_documents = documents
    if category:
        filtered_documents = [doc for doc in filtered_documents if doc.category == category]
        
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
#-----------------------------------------------------------------------------
# Get documents/resources pages
#-----------------------------------------------------------------------------

@app.get('/tutorials')
def tutorial():
    return model.tutorials()

@app.get('/assignments')
def assignment():
    return model.assignments()

@app.get('/other')
def other():
    return model.others()

@app.get('/lectures')
def lecture():
    return model.lectures()


#-----------------------------------------------------------------------------
# Admin actions
#-----------------------------------------------------------------------------

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
    unmute = request.forms.get('unmute')
    clear = request.forms.get('clear')
    global muted
    if clear:
        hash = SHA256.new()
        hash.update(clear.encode())
        clear = hash.hexdigest().encode()
        if database.user_authenticate("admin", clear):
            collections.deque.clear(messages)
            with open("./data/chat.pkl", "wb") as f:
                pickle.dump(messages, f)
            return model.page_view("delete", header=header, success="Successfully cleared chat!", error="")
        else:
            return model.page_view("delete", header=header, success="", error="Bad password.")
    if username:
        if not database.delete_user(username):
            return model.page_view("delete", header=header, success="", error="Failed to delete user (May not exist).")
        return model.page_view("delete", header=header, success=f"Successfully deleted {username}!", error="")
    if mute:
        if mute in database.passwords.keys():
            if mute != "admin":
                if mute not in muted:
                    muted.append(mute)
                    with open("./data/muted.pkl", "wb") as f:
                        pickle.dump(muted, f)
                    return model.page_view("delete", header=header, success=f"Successfully muted {mute}!", error="")
                else:
                    return model.page_view("delete", header=header, success="", error="User is already muted")
        return model.page_view("delete", header=header, success="", error="Failed to mute user (May not exist)")
    if unmute:
        if unmute in database.passwords.keys():
            if unmute != "admin":
                if unmute in muted:
                    muted.remove(unmute)
                    with open("./data/muted.pkl", "wb") as f:
                        pickle.dump(muted, f)
                    return model.page_view("delete", header=header, success=f"Successfully unmuted {unmute}!", error="")
                else:
                    return model.page_view("delete", header=header, success="", error="User is not muted")
        return model.page_view("delete", header=header, success="", error="Failed to unmute user (May not exist)")
    if filename:
        if not category:
            return model.page_view("delete", header=header, success="", error="Specify a category when deleting a file")
        global documents
        for doc in documents:
            if doc.name == filename and doc.category == category:
                documents.remove(doc)
                os.remove(doc.path)
                with open("./data/documents.pkl", "wb") as f:
                    pickle.dump(documents, f)
                return model.page_view("delete", header=header, success=f"Deleted {filename} in {category}.", error="")
        return model.page_view("delete", header=header, success="", error="File does not exist")
    return model.page_view("delete", header=header, success="", error="")

#-----------------------------------------------------------------------------
# Chat
#-----------------------------------------------------------------------------
@app.get('/chat')
def chat(channel="lobby"):
    user = verify()
    return model.chat(user, header)

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
    
    if nick not in muted:
        messages.append(Message(nick, text))
        with open("./data/chat.pkl", "wb") as f:
            pickle.dump(messages, f)
    else:
        return {'error': 'You are muted. Please contact an admin.'}
    return {'status': 'OK'}

@app.get('/api/fetch')
def on_fetch():
    ''' Return all messages '''
    # Fetch new messages
    updates = [m.json() for m in messages]
    return { 'messages': updates }


# Run the application
if __name__ == '__main__':
    run(app=session_app, host=host, port=port, debug=debug, server='gunicorn', certfile='./certs/info2222.project.crt', keyfile='./certs/info2222.project.key')