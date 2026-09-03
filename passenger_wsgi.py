import os
import sys

# Add this directory to path to locate manageCost
sys.path.insert(0, os.path.dirname(__file__))

# Load Django's WSGI application
from manageCost.wsgi import application