import functools
from typing import Optional

from flask import Blueprint, request, session, jsonify
from werkzeug.security import check_password_hash

from .config import ConfigManager

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def get_user_from_config(username: str):
    cfg = ConfigManager().get_config()
    for u in cfg.get("users", []):
        if u.get("username") == username:
            return u
    return None


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    user = get_user_from_config(username)
    if not user:
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401
    if not check_password_hash(user.get("password_hash", ""), password):
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401

    session["user"] = {"username": username, "role": user.get("role", "diag")}
    return jsonify({"ok": True, "role": user.get("role", "diag")})


@bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"ok": True})


def current_user() -> Optional[dict]:
    return session.get("user")


def require_role(min_role: str):
    order = {"diag": 0, "admin": 1, "root": 2}

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            u = current_user()
            if not u:
                return jsonify({"error": "unauthorized"}), 401
            if order.get(u.get("role", "diag"), 0) < order.get(min_role, 0):
                return jsonify({"error": "forbidden"}), 403
            return f(*args, **kwargs)

        return wrapper

    return decorator
