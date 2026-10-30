"""Public, non-sensitive endpoints: health check and client-facing configuration."""

from flask import Blueprint, current_app, jsonify

bp = Blueprint("meta", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.get("/config")
def public_config():
    """What the frontend needs to know before sign-up. Never exposes the invite code itself."""
    return jsonify({"invite_required": bool(current_app.config["INVITE_CODE"])})
