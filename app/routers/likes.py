from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from app.models.like import Like, LikeCreate
from app.models.user import User
from app.models.item import Item
from app.db import get_db

router = APIRouter(prefix="/likes", tags=["Likes"])

@router.post("/", response_model=Like)
async def create_like(like: LikeCreate, db: AsyncSession = Depends(get_db)):
    # Vérifier que l'utilisateur existe
    user = await db.get(User, like.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Vérifier que l'item existe
    item = await db.get(Item, like.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Vérifier si le like existe déjà
    existing_like = await db.execute(
        select(Like).where(
            (Like.user_id == like.user_id) & 
            (Like.item_id == like.item_id)
        )
    )
    if existing_like.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already liked")
    
    db_like = Like(**like.dict())
    db.add(db_like)
    await db.commit()
    await db.refresh(db_like)
    return db_like

@router.get("/user/{user_id}", response_model=List[Like])
async def read_user_likes(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(Like).where(Like.user_id == user_id)
    )
    return result.scalars().all()

@router.delete("/{like_id}")
async def delete_like(like_id: int, db: AsyncSession = Depends(get_db)):
    like = await db.get(Like, like_id)
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    await db.delete(like)
    await db.commit()
    return {"message": "Like removed"}