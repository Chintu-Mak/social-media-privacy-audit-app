from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from pathlib import Path

# Get backend root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from backend folder
load_dotenv(BASE_DIR / ".env")

MONGO_URI = os.getenv("MONGO_URI")

print("Loaded Mongo URI:", MONGO_URI)

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in .env file")
from .config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)

db = client["social_privacy_audit"]
users_collection = db["users"]