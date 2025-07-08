from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class MediaType(str, Enum):
    MOVIE = "movie"
    TV = "tv"
    GAME = "game"
    BOOK = "book"

class MediaBase(BaseModel):
    """Base commune pour tous les médias"""
    id: str
    title: str
    cover: Optional[str] = None
    media_type: MediaType

class MovieTVMedia(MediaBase):
    """DTO pour films et séries (TMDB)"""
    overview: Optional[str] = None
    release_date: Optional[str] = None
    poster_path: Optional[str] = None
    genres: List[str] = []
    
    @classmethod
    def from_tmdb(cls, data: dict, media_type: MediaType):
        return cls(
            id=str(data.get("id")),
            title=data.get("title") or data.get("name"),
            cover=f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else None,
            media_type=media_type,
            overview=data.get("overview"),
            release_date=data.get("release_date") or data.get("first_air_date"),
            poster_path=data.get("poster_path"),
            genres=[g["name"] for g in data.get("genres", [])]
        )

class GameMedia(MediaBase):
    """DTO pour jeux vidéo (RAWG)"""
    release_date: Optional[str] = None
    platforms: List[str] = []
    genres: List[str] = []
    rating: Optional[float] = None
    
    @classmethod
    def from_rawg(cls, data: dict):
        return cls(
            id=str(data.get("id")),
            title=data.get("name"),
            cover=data.get("background_image"),
            media_type=MediaType.GAME,
            release_date=data.get("released"),
            platforms=[p["platform"]["name"] for p in data.get("platforms", [])],
            genres=[g["name"] for g in data.get("genres", [])],
            rating=data.get("rating")
        )

class BookMedia(MediaBase):
    """DTO pour livres (Open Library)"""
    author: Optional[str] = None
    subjects: List[str] = []
    publish_date: Optional[str] = None
    
    @classmethod
    def from_openlibrary(cls, data: dict):
        return cls(
            id=data.get("olid") or data.get("key", "").replace("/works/", ""),
            title=data.get("title"),
            cover=f"https://covers.openlibrary.org/b/id/{data.get('cover_i')}-L.jpg" if data.get('cover_i') else None,
            media_type=MediaType.BOOK,
            author=data.get("author_name", [None])[0] if isinstance(data.get("author_name"), list) else data.get("author_name"),
            subjects=data.get("subjects", []),
            publish_date=data.get("first_publish_date")
        )

class MediaRecommendation(BaseModel):
    """DTO unifié pour les recommandations"""
    id: str
    title: str
    cover: Optional[str] = None
    media_type: MediaType
    # Champs communs optionnels
    release_date: Optional[str] = None
    genres: List[str] = []
    # Champs spécifiques
    overview: Optional[str] = None  # Films/séries
    platforms: List[str] = []       # Jeux
    author: Optional[str] = None    # Livres
    rating: Optional[float] = None  # Jeux
    
    @classmethod
    def from_movie_tv(cls, data: dict, media_type: MediaType):
        return cls(
            id=str(data.get("id")),
            title=data.get("title") or data.get("name"),
            cover=f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else None,
            media_type=media_type,
            release_date=data.get("release_date") or data.get("first_air_date"),
            genres=[g["name"] for g in data.get("genres", [])],
            overview=data.get("overview")
        )
    
    @classmethod
    def from_game(cls, data: dict):
        return cls(
            id=str(data.get("id")),
            title=data.get("name"),
            cover=data.get("background_image"),
            media_type=MediaType.GAME,
            release_date=data.get("released"),
            genres=[g["name"] for g in data.get("genres", [])],
            platforms=[p["platform"]["name"] for p in data.get("platforms", [])],
            rating=data.get("rating")
        )
    
    @classmethod
    def from_book(cls, data: dict):
        return cls(
            id=data.get("olid") or data.get("key", "").replace("/works/", ""),
            title=data.get("title"),
            cover=f"https://covers.openlibrary.org/b/id/{data.get('cover_i')}-L.jpg" if data.get('cover_i') else None,
            media_type=MediaType.BOOK,
            genres=data.get("subjects", []),
            author=data.get("author_name", [None])[0] if isinstance(data.get("author_name"), list) else data.get("author_name")
        ) 