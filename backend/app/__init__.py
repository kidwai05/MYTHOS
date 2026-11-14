import os
from flask import Flask, render_template, jsonify, request
from . import db as database
from .api import bp as api_bp
from .search import norm

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_app(config=None):
    app = Flask(__name__, template_folder=os.path.join(ROOT, 'frontend', 'templates'),
                static_folder=os.path.join(ROOT, 'frontend', 'static'), static_url_path='/static')
    app.config.update(DATABASE=os.environ.get('MYTHOS_DB', os.path.join(ROOT, 'mythos.db')))
    if config: app.config.update(config)
    app.json.ensure_ascii = False; app.json.sort_keys = False
    database.init_app(app)
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    def cat():
        from .api import catalog
        with app.app_context(): return catalog()

    @app.get('/')
    def home(): return render_template('index.html', title='Mythos: an encyclopedia of world mythology',
        description='Gods, heroes and monsters of Greek, Norse and Egyptian myth, each fact linked to the ancient text it comes from.')

    @app.get('/characters')
    def browse(): return render_template('browse.html', title='Browse characters | Mythos', description='Search and filter gods, heroes and monsters by mythology, role and domain.')

    @app.get('/characters/<slug>')
    def character_page(slug):
        c = cat().by_slug.get(slug)
        if not c: return render_template('error.html', title='Not found | Mythos', message=f"There is no character called '{slug}'."), 404
        roles = ', '.join(r for r in c['roles'])
        return render_template('character.html', slug=slug, title=f"{c['name']} ({c['mythology']['name']}) | Mythos",
            description=(c['summary'] or f"{c['name']}: {c['mythology']['name']} {roles}.")[:300])

    @app.get('/mythologies/<slug>')
    def mythology_page(slug):
        m = cat().mythologies.get(slug)
        if not m: return render_template('error.html', title='Not found | Mythos', message=f"There is no mythology called '{slug}'."), 404
        return render_template('mythology.html', slug=slug, title=f"{m['name']} mythology | Mythos", description=f"Characters and sources for {m['name']} mythology.")

    @app.errorhandler(404)
    def not_found(_e):
        if request.path.startswith('/api/'): return jsonify({'error': {'code': 'not_found', 'message': 'No such endpoint'}}), 404
        return render_template('error.html', title='Not found | Mythos', message='That page does not exist.'), 404
    return app
