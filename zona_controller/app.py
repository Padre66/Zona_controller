from pathlib import Path
import os

from flask import Flask, send_from_directory, render_template, redirect, url_for
from flask_session import Session

from .auth import bp as auth_bp, current_user
from .api import create_api_blueprint
from .state import State
from .udp_server import UDPServer
from .runtime_params import TDoARuntimeParams


def create_app(config_path: str = "zona.conf"):
    base_dir = Path(__file__).resolve().parent.parent
    web_dir = base_dir / "web"

    app = Flask(
        __name__,
        static_folder=str(web_dir / "static"),
        template_folder=str(web_dir / "templates"),
    )

    app.config["SECRET_KEY"] = "change-this-secret"
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)

    # Globális state
    state = State()

    # Runtime paraméterek (tdoa.runtime.* a zona.conf-ból)
    params = TDoARuntimeParams(config_path)
    app.config["runtime_params"] = params  # ha később másnak is kell

    # Anchor buffer méret beállítása induláskor
    buf_cfg = params.get_buffer_params()
    per_anchor_size = int(buf_cfg.get("per_anchor_size", 50))
    state.set_anchor_buffer_size(per_anchor_size)

    # Csak a "fő" processzben indítjuk el a UDP szervert:
    # - debug=False esetén egyszer indul (pl. Debian / production)
    # - debug=True esetén csak akkor, ha WERKZEUG_RUN_MAIN == "true"
    is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    if not app.debug or is_reloader_child:
        udp_server = UDPServer(config_path, state)
        udp_server.start()

    app.register_blueprint(auth_bp)
    api_bp = create_api_blueprint(state, config_path)
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        if not current_user():
            return redirect(url_for("login_page"))
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/map")
    def map_page():
        if not current_user():
            return redirect(url_for("login_page"))
        return render_template("map.html")

    @app.route("/config")
    def config_page():
        if not current_user():
            return redirect(url_for("login_page"))
        return render_template("config.html")

    @app.route("/static/<path:filename>")
    def static_files(filename):
        static_dir = web_dir / "static"
        return send_from_directory(static_dir, filename)

    return app
