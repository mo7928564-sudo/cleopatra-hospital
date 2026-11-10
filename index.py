import os
import sys

# Ensure parent directory is in Python path so server.py and its assets can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from server import app

# Export app for Vercel Serverless
# Vercel's ASGI bridge will automatically detect and run `app`
