from flask import Blueprint, jsonify, request

from .auth import require_role, current_user
from .config import ConfigManager
from .state import State

bp = Blueprint("api", __name__, url_prefix="/api")


def create_api_blueprint(state: State, config_path: str):
    cfg_mgr = ConfigManager(config_path)

    @bp.route("/status", methods=["GET"])
    @require_role("diag")
    def status():
        return jsonify({
            "status": "ok",
            "last_msg": state.get_last_message(),
            "tags": state.get_all_tag_positions()
        })

    @bp.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @bp.route("/config", methods=["GET"])
    @require_role("diag")
    def get_config():
        cfg = cfg_mgr.get_config()
        user = current_user()
        role = user.get("role", "diag") if user else "diag"
        if role != "root":
            if "crypto" in cfg and "aes_key_hex" in cfg["crypto"]:
                cfg["crypto"]["aes_key_hex"] = "***"
        return jsonify(cfg)

    @bp.route("/config", methods=["PATCH"])
    @require_role("admin")
    def patch_config():
        updates = request.get_json(force=True, silent=True) or {}
        user = current_user()
        role = user.get("role", "diag") if user else "diag"
        try:
            cfg_mgr.update_from_dict(updates, role)
        except PermissionError as e:
            return jsonify({"error": str(e)}), 403
        return jsonify({"ok": True})

    @bp.route("/anchors", methods=["GET"])
    @require_role("diag")
    def get_anchors():
        cfg = cfg_mgr.get_config()
        tdoa = cfg.get("tdoa", {})
        return jsonify(tdoa.get("anchors", []))

    @bp.route("/anchors", methods=["POST"])
    @require_role("admin")
    def add_anchor():
        data = request.get_json(force=True, silent=True) or {}
        cfg = cfg_mgr.get_config()
        tdoa = cfg.setdefault("tdoa", {})
        anchors = tdoa.setdefault("anchors", [])
        anchors.append(data)
        cfg_mgr.update_from_dict({"tdoa": tdoa}, current_user().get("role", "admin"))
        return jsonify({"ok": True})

    @bp.route("/anchors/<anchor_id>", methods=["PUT"])
    @require_role("admin")
    def update_anchor(anchor_id):
        data = request.get_json(force=True, silent=True) or {}
        cfg = cfg_mgr.get_config()
        tdoa = cfg.setdefault("tdoa", {})
        anchors = tdoa.setdefault("anchors", [])
        for a in anchors:
            if a.get("id") == anchor_id:
                a.update(data)
                break
        cfg_mgr.update_from_dict({"tdoa": tdoa}, current_user().get("role", "admin"))
        return jsonify({"ok": True})

    @bp.route("/anchors/<anchor_id>", methods=["DELETE"])
    @require_role("root")
    def delete_anchor(anchor_id):
        cfg = cfg_mgr.get_config()
        tdoa = cfg.setdefault("tdoa", {})
        anchors = tdoa.setdefault("anchors", [])
        anchors = [a for a in anchors if a.get("id") != anchor_id]
        tdoa["anchors"] = anchors
        cfg_mgr.update_from_dict({"tdoa": tdoa}, current_user().get("role", "root"))
        return jsonify({"ok": True})

    @bp.route("/tdoa/tags", methods=["GET"])
    @require_role("diag")
    def list_tags():
        cfg = cfg_mgr.get_config()
        tdoa = cfg.get("tdoa", {})
        return jsonify(tdoa.get("tags", []))

    @bp.route("/tdoa/position", methods=["GET"])
    @require_role("diag")
    def get_position():
        tag_id = request.args.get("tag_id")
        if not tag_id:
            return jsonify({"error": "tag_id required"}), 400
        pos = state.get_tag_position(tag_id)
        if not pos:
            return jsonify({"error": "not_found"}), 404
        return jsonify({"tag_id": tag_id, **pos})

    return bp
