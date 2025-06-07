from fastapi import APIRouter, Depends, HTTPException, status
from ..services.tmdb_client import get_top_movies

router = APIRouter()

@router.get("/top-movies")
def get_top_movies_tmdb():
    return get_top_movies("day")