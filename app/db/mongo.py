from pymongo import MongoClient
from ..config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["recommendation_db"]
users_collection = db["users"]
interactions_collection = db["interactions"]
