"""
Health profile HTTP layer (Module 3). Same trust model as the rest of the
app currently: the frontend sends the logged-in user's email with each
request (from MA.getSession()) -- not a real server-side session yet.
"""
from flask import Blueprint, request, jsonify

from backend.services.profile_service import get_profile, save_profile

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/api/profile", methods=["GET"])
def get_profile_route():
    email = (request.args.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "email is required"}), 400

    try:
        profile = get_profile(email)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify(profile), 200


@profile_bp.route("/api/profile", methods=["POST"])
def save_profile_route():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "email is required"}), 400

    try:
        updated = save_profile(email, data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify(updated), 200