# This file provides a very simple "no sql database using python dictionaries"
# If you don't know SQL then you might consider something like this for this course
# We're not using a class here as we're roughly expecting this to be a singleton

# If you need to multithread this, a cheap and easy way is to stick it on its own bottle server on a different port
# Write a few dispatch methods and add routes

# A heads up, this code is for demonstration purposes; you might want to modify it for your own needs
# Currently it does basic insertions and lookups
import pickle, bcrypt
import os.path
from Crypto.Hash import SHA256

salt_table = "salt.pkl"
pass_table = "pass.pkl"
class DB():
    '''
    This is a singleton class that handles all the tables
    You'll probably want to extend this with features like multiple lookups, and deletion
    A method to write to and load from file might also be useful for your purposes
    '''
    def __init__(self):
        self.passwords = {}
        self.salt = {}

    def save_tables(self):
        with open(pass_table, "wb") as f:
            pickle.dump(self.passwords, f)
        with open(salt_table, "wb") as f:
            pickle.dump(self.salt, f)
    
    def load(self):
        if not os.path.isfile(pass_table) and not os.path.isfile(salt_table):
            return
        with open(pass_table, "rb") as f:
            self.passwords = pickle.load(f)
        with open(salt_table, "rb") as f:
            self.salt = pickle.load(f)
        
    def user_authenticate(self, user, password):
        if not self.exists(user):
            return False
        hash = SHA256.new()
        hash.update((self.salt[user] + password))
        return True if hash.hexdigest() == self.passwords[user] else False
        
    def add_user(self, user, password):
        while True: 
            gen_salt = bcrypt.gensalt()
            if gen_salt not in self.salt.values():
                break
        self.salt[user] = gen_salt
        hash = SHA256.new()
        hash.update((gen_salt + password))
        self.passwords[user] = hash.hexdigest()
        
    def exists(self, user):
        if user in self.passwords.keys():
            return True
        return False
        

# Our global database
# Invoke this as needed
database = DB()
