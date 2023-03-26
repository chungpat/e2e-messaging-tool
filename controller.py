'''
    This file will handle our typical Bottle requests and responses 
    You should not have anything beyond basic page loads, handling forms and 
    maybe some simple program logic
'''

from bottle import route, get, post, error, request, static_file
from Crypto.Hash import SHA256
import model

user = ""

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
    return model.index(user)

#-----------------------------------------------------------------------------

# Display the login page
@get('/login')
def get_login_controller():
    '''
        get_login
        
        Serves the login page
    '''
    return model.login_form()

#-----------------------------------------------------------------------------


@get('/logout')
def logout():
    global user
    user = ""
    return model.logout()

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
    # Handle the form processing
    username = request.forms.get('username')
    password = request.forms.get('password')
    hash = SHA256.new()
    hash.update(password.encode())
    password = hash.hexdigest().encode()
    
    # Call the appropriate method
    if model.login_check(username, password):
        user = username
        return model.page_view("valid", name=username)
    else:   
        return model.page_view("invalid", reason="Invalid username or password/User doesn't exist")



#-----------------------------------------------------------------------------

# Display the register page
@get('/register')
def get_register_controller():

    return model.register()

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
    return model.register_check(username, password, password_c, length, upper, num, special)


#-----------------------------------------------------------------------------

@get('/about')
def get_about():
    '''
        get_about
        
        Serves the about page
    '''
    return model.about()
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
