import sys
import os

# Insert project root at position 0 BEFORE any project imports.
# This ensures `from profile import *` in main.py finds our profile.py
# rather than Python's built-in profile module.
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

from main import zevio as app
