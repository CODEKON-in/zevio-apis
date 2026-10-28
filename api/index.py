import sys
import os

# Make the project root importable so all modules (db, auth, etc.) resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import zevio as app
