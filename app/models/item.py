from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from enum import Enum

class ItemType(str, Enum):
    MOVIE = "movie"
    SERIES = "series"
    BOOK = "book"

class ItemBase(SQLModel):
    title: str = Field(index=True)
    description: Optional[str] = None
    type: ItemType 
    genre: Optional[str] = None

class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    likes: List["Like"] = Relationship(back_populates="item")

class ItemCreate(ItemBase):
    pass