import os
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
print("Key present:", bool(api_key))  # if False, that's your whole problem

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Say hello",
)
print(response.text)