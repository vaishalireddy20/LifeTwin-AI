from pathlib import Path
import os
import secrets
from flask import Flask
from .db import init_db, seed_demo
from .routes import main

# Project root: LifeTwin_AI/
BASE_DIR = Path(__file__).resolve().parent.parent


def create_app():
    """Create and configure the LifeTwin AI Flask application."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        # Templates and static files are stored at the project root.
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
        static_url_path="/static",
    )

    app.config.update(
        # A new development key is generated on every server start so an old
        # browser session cannot silently bypass the login screen. In production,
        # set LIFETWIN_SECRET_KEY to a stable secret.
        SECRET_KEY=os.environ.get("LIFETWIN_SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        DATABASE=str(BASE_DIR / "instance" / "lifetwin.db"),
    )

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db(app.config["DATABASE"])
    seed_demo(app.config["DATABASE"])
    app.register_blueprint(main)
    return app
