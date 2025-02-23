from fastapi import FastAPI
from sqlmodel import SQLModel
from app.db import engine, async_engine
from app.routers import users, likes, items

app = FastAPI()

app.include_router(users.router)
app.include_router(items.router)
app.include_router(likes.router)

@app.on_event("startup")
async def on_startup():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

@app.get("/")
def root():
    return {"message": "Shitzer Recommendation API"}