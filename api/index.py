import sys
import os
import traceback

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

try:
    from main import zevio as app
except Exception as e:
    from flask import Flask, jsonify
    app = Flask('fallback_error_app')
    _err_msg = str(e)
    _err_tb = traceback.format_exc()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return jsonify({
            'status': 'error',
            'message': 'Application failed to start on Vercel',
            'error': _err_msg,
            'traceback': _err_tb.splitlines()
        }), 500
