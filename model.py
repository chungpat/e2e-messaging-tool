'''
    Our Model class
    This should control the actual "logic" of your website
    And nicely abstracts away the program logic from your page loading
    It should exist as a separate layer to any database or data structure that you might be using
    Nothing here should be stateful, if it's stateful let the database handle it
'''
import view
from no_sql_db import database

# Initialise our views, all arguments are defaults for the template
page_view = view.View()

#-----------------------------------------------------------------------------
# Index
#-----------------------------------------------------------------------------

def index(username, header):
    '''
        index
        Returns the view for the index
    '''
    if (not username):
        username = "User"
    users = [name for name in database.passwords.keys()]
    if "admin" in users:
        users.remove("admin")
    if not users:
        users = "No users"
    return page_view("index", name=username, data=users, header=header)

#-----------------------------------------------------------------------------
# Login
#-----------------------------------------------------------------------------

def login_form(header):
    '''
        login_form
        Returns the view for the login_form
    '''
    return page_view("/account/login", error_msg="", header=header)

# Check the login credentials
def login_check(username, password):
    database.load()
    return database.user_authenticate(username, password)

#-----------------------------------------------------------------------------
# Logout
#-----------------------------------------------------------------------------

def logout(header):
    '''
        login_form
        Returns the view for the login_form
    '''
    return page_view("/account/logout", header=header)

#-----------------------------------------------------------------------------
# Chat
#-----------------------------------------------------------------------------

def chat(user, header):
    if not user:
        return page_view("/account/login", error_msg="", header=header)
    else:
        return page_view("chat", header=header)

#-----------------------------------------------------------------------------
# Upload
#-----------------------------------------------------------------------------
def upload(user, header):
    if not user:
        return page_view("/account/login", error_msg="", header=header)
    return page_view.load_template("upload")

#-----------------------------------------------------------------------------
# Delete
#-----------------------------------------------------------------------------
def delete(user, header):
    if (user != "admin"):
        return index(username=user, header=header)
    return page_view("delete", header=header, reason="")

#-----------------------------------------------------------------------------
# Documents
#-----------------------------------------------------------------------------
def lectures():
    return page_view.load_template("/resources/lecture")

def tutorials():
    return page_view.load_template("/resources/tutorial")

def assignments():
    return page_view.load_template("/resources/assignment")

def others():
    return page_view.load_template("/resources/other")

#-----------------------------------------------------------------------------
# Register
#-----------------------------------------------------------------------------

def register(header):
    '''
        index
        Returns the view for the index
    '''
    return page_view("/account/register", header=header, error="", success="")

#-----------------------------------------------------------------------------

# Check the register credentials
def register_check(username, password, password_c, pass_length, upper, num, special, header):
    database.load()
    register = True
    if password != password_c:
        err_str = "Passwords weren't the same."
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
        return page_view("/account/register", header=header, error="", success="Successfully registered!")
    else:
        return page_view("/account/register", header=header, error=err_str, success="")
