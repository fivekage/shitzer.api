from fastapi import FastAPI
from .routers import recommendation, auth, tmdb

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(recommendation.router, prefix="/api", tags=["recommendation"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tmdb.router, prefix="/api/tmdb", tags=["tmdb"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)