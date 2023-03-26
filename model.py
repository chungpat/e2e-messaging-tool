'''
    Our Model class
    This should control the actual "logic" of your website
    And nicely abstracts away the program logic from your page loading
    It should exist as a separate layer to any database or data structure that you might be using
    Nothing here should be stateful, if it's stateful let the database handle it
'''
import view
import random
from no_sql_db import database

# Initialise our views, all arguments are defaults for the template
page_view = view.View()

#-----------------------------------------------------------------------------
# Index
#-----------------------------------------------------------------------------

def index(username):
    '''
        index
        Returns the view for the index
    '''
    if (not username):
        username = "User"
    return page_view("index", name=username)

#-----------------------------------------------------------------------------
# Login
#-----------------------------------------------------------------------------

def login_form():
    '''
        login_form
        Returns the view for the login_form
    '''
    return page_view("login")

#-----------------------------------------------------------------------------
# Logout
#-----------------------------------------------------------------------------

def logout():
    '''
        login_form
        Returns the view for the login_form
    '''
    return page_view("logout")


#-----------------------------------------------------------------------------
# Register
#-----------------------------------------------------------------------------

def register():
    '''
        index
        Returns the view for the index
    '''
    return page_view("register")

#-----------------------------------------------------------------------------

# Check the login credentials
def register_check(username, password, password_c, pass_length, upper, num, special):
    database.load()
    register = True
    if password != password_c:
        err_str = "Passwords weren't the same."
        register = False
    elif not username:
        err_str = "Empty username field"
        register = False
    elif pass_length <= 10:
        err_str = "Password is too short."
        register = False
    elif not upper or not num or not special:
        err_str = "Password must contain at least an uppercase character,number and special character"
        register = False
    elif database.exists(username):
        err_str = "User already exists, please login"
        register = False
    if register: 
        database.add_user(username, password)
        database.save_tables()
        return page_view("register_valid")
    else:
        return page_view("register_invalid", reason=err_str)

# Check the login credentials
def login_check(username, password):
    database.load()
    # By default assume good creds
    return database.user_authenticate(username, password)
#-----------------------------------------------------------------------------
# About
#-----------------------------------------------------------------------------

def about():
    '''
        about
        Returns the view for the about page
    '''
    return page_view("about", garble=about_garble())



# Returns a random string each time
def about_garble():
    '''
        about_garble
        Returns one of several strings for the about page
    '''
    garble = ["leverage agile frameworks to provide a robust synopsis for high level overviews.", 
    "iterate approaches to corporate strategy and foster collaborative thinking to further the overall value proposition.",
    "organically grow the holistic world view of disruptive innovation via workplace change management and empowerment.",
    "bring to the table win-win survival strategies to ensure proactive and progressive competitive domination.",
    "ensure the end of the day advancement, a new normal that has evolved from epistemic management approaches and is on the runway towards a streamlined cloud solution.",
    "provide user generated content in real-time will have multiple touchpoints for offshoring."]
    return garble[random.randint(0, len(garble) - 1)]


#-----------------------------------------------------------------------------
# Debug
#-----------------------------------------------------------------------------

def debug(cmd):
    try:
        return str(eval(cmd))
    except:
        pass


#-----------------------------------------------------------------------------
# 404
# Custom 404 error page
#-----------------------------------------------------------------------------

def handle_errors(error):
    error_type = error.status_line
    error_msg = error.body
    return page_view("error", error_type=error_type, error_msg=error_msg)