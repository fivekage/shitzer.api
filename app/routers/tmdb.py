from fastapi import APIRouter, Depends, HTTPException, status
from ..services.tmdb_client import get_top_movies, get_movie_info, get_recommendations_from_movie

router = APIRouter()

@router.get("/movie/top")
def get_top_movies_tmdb():
    return get_top_movies("day")

@router.get("/movie/{tmdb_id}")
def get_movie_tmdb(tmdb_id: str):
    return get_movie_info(tmdb_id)

@router.get("/movie/{tmdb_id}/recommendations")
def get_recommendations_from_movie_tmdb(tmdb_id: str):
    return get_recommendations_from_movie(tmdb_id)