from pydantic import BaseModel
from typing import List, Optional

class RecommendationRequest(BaseModel):
    user_id: Optional[str] = None
    liked_tmdb_ids: List[str]