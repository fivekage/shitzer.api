from pydantic import BaseModel
from typing import List, Optional

class UserInteractions(BaseModel):
    user_id: str
    liked_ids: dict = {}  # media_type -> List[str]
    disliked_ids: dict = {}  # media_type -> List[str]

class User(BaseModel):
    id: Optional[str] = None
    email: str
    username: str
    hashed_password: str
