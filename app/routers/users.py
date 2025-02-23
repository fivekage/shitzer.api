from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User, UserCreate 
from app.db import get_db

router = APIRouter()

@router.post("/users/", response_model=User)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # TODO: Il faudra hashé le mdp
    hashed_password = f"hashed_{user.password}"
    
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=user.is_active
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user