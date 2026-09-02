from backend.database.mongo import users_collection
result = users_collection.delete_many({'email': {'$in': ['your-real-email@gmail.com', 'hasinipericharla10@gmail.com']}})
print(f'Deleted {result.deleted_count} test user(s).')
