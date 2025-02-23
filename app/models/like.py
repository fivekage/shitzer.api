from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional

class LikeBase(SQLModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Like(LikeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    item_id: int = Field(foreign_key="item.id")

    user: Optional["User"] = Relationship(back_populates="likes")
    item: Optional["Item"] = Relationship(back_populates="likes")

class LikeCreate(LikeBase):
    user_id: int
    item_id: int