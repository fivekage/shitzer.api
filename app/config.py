from dotenv import load_dotenv
import os

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = "mongodb://root:example@localhost:27017"
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

print("MONGO_URI utilisé:", MONGO_URI)
