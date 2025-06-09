from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import recommendation, auth, tmdb
from . import config

app = FastAPI()

origins = [
    config.CLIENT_ORIGIN,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(recommendation.router, prefix="/api", tags=["recommendation"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tmdb.router, prefix="/api/tmdb", tags=["tmdb"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)