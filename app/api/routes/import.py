import json
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb+srv://yatharthchaudhary:yatharthmetasquare@cluster0.bojt8wm.mongodb.net/")
db = client["workoutbuddy"]
collection = db["exercise_library"]

# Load exercise data from JSON file
with open(r"E:\Desktop\WorkOutBuddy\app\api\routes\exercises.json", "r") as f:
    exercises = json.load(f)

# Optional: clean old data
collection.delete_many({})

# Insert into collection
collection.insert_many(exercises)

print(f"✅ Inserted {len(exercises)} exercises into MongoDB.")
