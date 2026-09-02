"""
Auth HTTP layer: signup (sends OTP email), OTP verification, login.
Thin by design -- all real logic lives in auth_service.py.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_mail import Message

from backend.services.auth_service import (
    create_user_and_generate_otp,
    verify_otp,
    authenticate_user,
)

auth_bp = Blueprint("auth", __name__)


def _send_otp_email(to_email: str, otp: str):
    mail = current_app.extensions["mail"]
    msg = Message(
        "Your MedAssist AI verification code",
        sender=current_app.config["MAIL_USERNAME"],
        recipients=[to_email],
    )
    msg.body = (
        f"Your verification code is: {otp}\n\n"
        f"This code expires in 10 minutes. If you didn't request this, ignore this email."
    )
    mail.send(msg)


@auth_bp.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 400

    try:
        otp = create_user_and_generate_otp(name, email, password)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        _send_otp_email(email, otp)
    except Exception:
        current_app.logger.exception("Failed to send OTP email to %s", email)
        return jsonify({"error": "Could not send verification email. Please try again."}), 502

    return jsonify({"message": "Verification code sent to your email."}), 201


@auth_bp.route("/api/verify-otp", methods=["POST"])
def verify_otp_route():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()

    if not email or not code:
        return jsonify({"error": "email and code are required"}), 400

    try:
        verify_otp(email, code)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "Email verified successfully."}), 200


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    try:
        user = authenticate_user(email, password)
    except ValueError as e:
        status = 403 if "verify" in str(e).lower() else 401
        return jsonify({"error": str(e)}), status

    return jsonify({"message": "Login successful", "name": user["name"]}), 200