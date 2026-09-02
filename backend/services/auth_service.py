"""
Auth business logic: signup (with email OTP), login, OTP verification.
Kept free of Flask imports (no `request`/`jsonify` here) so it's testable
in isolation.
"""
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from backend.database.mongo import users_collection

OTP_EXPIRY_MINUTES = 10


def _generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def create_user_and_generate_otp(name: str, email: str, password: str) -> str:
    """
    Creates (or refreshes) an unverified user document and returns a new OTP.
    Raises ValueError if the email already belongs to a VERIFIED account.
    If the email exists but was never verified (e.g. they abandoned signup
    partway), this overwrites it with fresh details and a new code -- so
    users aren't stuck if they mistype something and retry.
    """
    existing = users_collection.find_one({"email": email})
    if existing and existing.get("is_verified"):
        raise ValueError("Email already registered")

    otp = _generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    users_collection.update_one(
        {"email": email},
        {"$set": {
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "is_verified": False,
            "otp_code": otp,
            "otp_expires_at": expires_at,
        }},
        upsert=True,
    )
    return otp


def verify_otp(email: str, code: str) -> None:
    """Raises ValueError with a user-facing message on any failure."""
    user = users_collection.find_one({"email": email})
    if not user:
        raise ValueError("No pending signup found for this email.")
    if user.get("is_verified"):
        raise ValueError("This account is already verified.")

    expires_at = user.get("otp_expires_at")
    if expires_at is None or datetime.utcnow() > expires_at:
        raise ValueError("Code expired. Please sign up again to get a new one.")

    if user.get("otp_code") != code:
        raise ValueError("Incorrect verification code.")

    users_collection.update_one(
        {"email": email},
        {"$set": {"is_verified": True}, "$unset": {"otp_code": "", "otp_expires_at": ""}},
    )


def authenticate_user(email: str, password: str) -> dict:
    """Returns the user dict on success. Raises ValueError on any failure,
    with a message safe to show the client."""
    user = users_collection.find_one({"email": email})
    if not user or not check_password_hash(user["password_hash"], password):
        raise ValueError("Invalid email or password")
    if not user.get("is_verified"):
        raise ValueError("Please verify your email before logging in")
    return user