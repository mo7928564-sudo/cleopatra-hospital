import os
import sys

# Vercel sets VERCEL=1 in environment
os.environ["VERCEL"] = "1"

# Add project root to Python path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from server import app
