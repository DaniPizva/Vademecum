#db\mongo.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
 
load_dotenv()
 
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
 
client = MongoClient(MONGO_URI)
mongo_db = client[MONGO_DB_NAME]
 
 
def get_mongo_db():
    return mongo_db