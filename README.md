To run the program: python3 controller.py

## Overview ##

This web-app has been roughly set up around a 'Model View Controller' or MVC design to keep the logic of the code and the logic of the site separate. This splits the functions the app into 3 categories:

- Models (Python Bottle Server): Handles the program logic
- Views (Javascript, HTML, CSS): Handles the returned HTML pages
- Controllers (SQL): Handles the requests for pages that the user sends

## Admin page ##

Admins can mute/unmute any user and delete any file in the 'documents' section of the app.
	This page can be access by:
    Logging in as an administrator: Username - ‘admin’, password - ‘Jasonkam123.’
    Navigate to the Home page.
    Click the university phone number in the footer of the page.
