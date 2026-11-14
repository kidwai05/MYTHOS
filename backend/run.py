#!/usr/bin/env python3
"""Run the development server from the repo root:  python backend/run.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app import create_app
if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)), debug=os.environ.get('DEBUG') == '1')
