"""
WSGI configuration for Verdict AI Backend.
This file is used by Gunicorn to serve the Flask application.
"""

import os
from app import app

if __name__ == "__main__":
    app.run()
