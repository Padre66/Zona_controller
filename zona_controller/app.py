from pathlib import Path
import os
from datetime import timedelta

from flask import (
    Flask,
    send_from_directory,
    render_template,
    redirect,
    url_for,
    session,
    request,
)
from flask_session import Session

from .auth import bp as auth_bp, current_user
from .api import create_api_blueprint
from .state import State
from .udp_server import UDPServer
from .tdoa import TDoAProcessor
from .runtime_params import TDoARuntimeParams
from .config import ConfigManager

def create_app(config_path: str = "zona.conf"):
    base_dir = Path(__file__).resolve().parent.parent
    web_dir = base_dir / "web"

    app = Flask(
        __name__,
        static_folder=str(web_dir / "static"),
        template_folder=str(web_dir / "templates"),
    )

    # Config beolvasás (zona.conf)
    cfg_mgr = ConfigManager(config_path)
    cfg = cfg_mgr.get_config()
    web_cfg = cfg.get("web", {})
    session_timeout_sec = int(web_cfg.get("session_timeout_sec", 1800))

    # Session beállítások
    app.config["SECRET_KEY"] = "change-this-secret"
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=session_timeout_sec)

    Session(app)

    # Globális state
    state = State()

    # Runtime paraméterek (tdoa.runtime.* a zona.conf-ból)
    params = TDoARuntimeParams(config_path)
    app.config["runtime_params"] = params  # ha később másnak is kell

    # Anchor buffer méret beállítása induláskor
    buf_cfg = params.get_buffer_params()
    per_anchor_size = int(buf_cfg.get("per_anchor_size", 50))
    processor = TDoAProcessor(state, params)
    state.set_anchor_buffer_size(per_anchor_size)

    # Csak a "fő" processzben indítjuk el a UDP szervert:
    # - debug=False esetén egyszer indul (pl. Debian / production)
    # - debug=True esetén csak akkor, ha WERKZEUG_RUN_MAIN == "true"
    is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    if not app.debug or is_reloader_child:
        udp_server = UDPServer(config_path, state, processor, params)
        udp_server.start()

    app.register_blueprint(auth_bp)
    api_bp = create_api_blueprint(state, config_path)
    app.register_blueprint(api_bp)

    # Minden endpoint előtt lefut: ha nem vagy bejelentkezve, login oldalra visz
    @app.before_request
    def require_login_for_all():
        # Mindig engedett útvonalak:
        # - login oldal
        # - auth API (login/logout)
        # - statikus fájlok
        path = request.path or ""

        if path.startswith("/static/"):
            return None
        if path.startswith("/api/auth/"):
            return None
        if path == "/login":
            return None

        # Ha nincs user a sessionben → login oldal
        if not current_user():
            return redirect(url_for("login_page"))

    @app.route("/")
    def index():
        if not current_user():
            return redirect(url_for("login_page"))
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/logout", methods=["GET", "POST"])
    def logout_page():
        # töröljük a user-t a sessionből
        session.pop("user", None)
        # vissza a login oldalra
        return redirect(url_for("login_page"))

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
