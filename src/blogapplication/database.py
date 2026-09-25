from pymongo import MongoClient

mongo_url = "mongodb+srv://testuser:e2t2THGDnCZRwIdr@cluster0.fdwibcx.mongodb.net/?appName=Cluster0"

mongo_client = MongoClient(mongo_url)

db = mongo_client["blogappdb"]

users = db["users"]
blogs = db["blogs"]
comments = db["comments"]
likes = db["likes"]