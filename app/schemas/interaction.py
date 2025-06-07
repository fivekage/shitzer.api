from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Mood(str, Enum):
    CHILL = "chill"
    EVASION = "evasion"
    ACTION = "action"
    SUSPENSE = "suspense"
    HORREUR = "horreur"

class RecommendationRequest(BaseModel):
    user_id: Optional[str] = None
    liked_tmdb_ids: List[str]

class LikeRequest(BaseModel):
    movie_id: str

class MoodRecommendationRequest(BaseModel):
    mood: Mood