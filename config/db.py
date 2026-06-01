import os
from pymongo import MongoClient

# Use local MongoDB by default or env variable
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["aquasetu"]
