from fastapi import APIRouter, Depends, HTTPException, status, Query
from ..services.tmdb_client import get_top_movies, get_movie_info, get_recommendations_from_movie
from ..services.rawg_client import get_top_games

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

@router.get("/game/top")
def get_top_games_rawg(
    year: int = Query(None, description="Année (par défaut année en cours)"),
    ordering: str = Query("-added", description="Tri RAWG : -added, -rating, -released, etc."),
    page_size: int = Query(10, description="Nombre de jeux à retourner")
):
    """Top jeux vidéo de l'année (ou d'une année donnée) via RAWG.io"""
    return get_top_games(year=year, ordering=ordering, page_size=page_size)