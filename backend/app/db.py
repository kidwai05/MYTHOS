import os, sqlite3
from flask import g, current_app

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

def close_db(_exc=None):
    db = g.pop('db', None)
    if db is not None: db.close()

def init_app(app):
    """Build the database from data/*.json if it does not exist yet, then register the teardown."""
    path = app.config['DATABASE']
    if not os.path.exists(path):
        from ..seed.loader import build
        build(path)
    app.teardown_appcontext(close_db)
