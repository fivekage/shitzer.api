from fastapi import APIRouter, HTTPException, status, Depends
from ..schemas.user import UserCreate, UserLogin, UserResponse, Token
from ..db.mongo import users_collection
from ..services.auth import hash_password, verify_password, create_access_token
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    hashed_pwd = hash_password(user.password)
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_pwd
    del user_dict["password"]
    result = users_collection.insert_one(user_dict)
    return UserResponse(id=str(result.inserted_id), email=user.email, username=user.username)

@router.post("/login", response_model=Token)
def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    access_token = create_access_token({"sub": str(db_user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"} 