"""
Health profile business logic (Module 3). Profile fields live directly on
the user's MongoDB document (same collection as auth), since a health
profile always belongs to exactly one user -- no need for a separate
collection.
"""
from backend.database.mongo import users_collection

PROFILE_FIELDS = ["name", "age", "gender", "heightCm", "weightKg", "history", "allergies"]


def get_profile(email: str) -> dict:
    """Returns the profile subset of the user doc. Raises ValueError if no
    such user exists."""
    user = users_collection.find_one({"email": email}, {"_id": 0, **{f: 1 for f in PROFILE_FIELDS}})
    if user is None:
        raise ValueError("User not found")
    return {field: user.get(field) for field in PROFILE_FIELDS}


def save_profile(email: str, profile_data: dict) -> dict:
    """Updates only the known profile fields on the user's doc -- ignores
    any unexpected keys in profile_data instead of blindly trusting input.
    Raises ValueError if no such user exists."""
    update = {field: profile_data.get(field) for field in PROFILE_FIELDS if field in profile_data}

    result = users_collection.update_one({"email": email}, {"$set": update})
    if result.matched_count == 0:
        raise ValueError("User not found")

    return get_profile(email)