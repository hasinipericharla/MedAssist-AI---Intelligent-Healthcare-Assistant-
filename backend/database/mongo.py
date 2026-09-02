"""
MongoDB connection setup. Single client instance, initialized once at
import time (not per-request) since MongoClient handles its own internal
connection pooling.
"""
import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["MedicalAI"]  # explicit name, doesn't depend on URI path  

users_collection = db.users

# Enforce uniqueness at the DB level -- app-level checks alone can race
# under concurrent signups.
users_collection.create_index("email", unique=True)