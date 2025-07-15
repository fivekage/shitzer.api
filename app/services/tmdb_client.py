import requests
from typing import Optional
from ..config import TMDB_API_KEY, RAWG_API_KEY
from .rawg_client import search_game, get_game_info
from .openlibrary_client import search_book, get_book_info

TMDB_BASE_URL = "https://api.themoviedb.org/3"

def get_top_media(media_type: str = "movie", time_window: str = "day") -> list[dict]:
    """
    Récupère les médias les plus populaires (films, séries, etc.).
    """
    url = f"{TMDB_BASE_URL}/trending/{media_type}/{time_window}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR",
        "page": 1
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("results", [])

def get_media_info(media_type: str, media_id: str) -> dict:
    """
    Récupère les informations détaillées d'un média à partir de son ID.
    - Pour 'movie' ou 'tv' : id TMDB
    - Pour 'game' : id RAWG
    - Pour 'book' : id OpenLibrary (OLID)
    """
    if media_type == "game":
        return get_game_info(media_id)
    if media_type == "book":
        return get_book_info(media_id)
    url = f"{TMDB_BASE_URL}/{media_type}/{media_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def search_media(media_type: str, title: str) -> Optional[dict]:
    """
    Recherche un média par son titre et retourne le premier résultat.
    - Pour 'movie' ou 'tv' : id TMDB
    - Pour 'game' : id RAWG
    - Pour 'book' : id OpenLibrary (OLID)
    """
    if media_type == "game":
        return search_game(title)
    if media_type == "book":
        return search_book(title)
    url = f"{TMDB_BASE_URL}/search/{media_type}"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "fr-FR"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    results = response.json().get("results", [])
    if results:
        return results[0]
    return None

def get_recommendations_from_media(media_type: str, tmdb_id: str) -> list[dict]:
    """
    Récupère les recommandations d'un média à partir de son ID TMDB.
    """
    url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}/recommendations"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("results", [])

def build_prompt_from_liked_media(media_type: str, tmdb_ids: list[str]) -> str:
    """
    Construit un prompt textuel basé sur les médias likés pour le LLM.
    """
    liked_media = []
    for tmdb_id in tmdb_ids:
        try:
            data = get_media_info(media_type, tmdb_id)
            if media_type == "game":
                title = data.get("name", "Inconnu")
                genres = [g["name"] for g in data.get("genres", [])]
            elif media_type == "book":
                title = data.get("title", "Inconnu")
                genres = data.get("subjects", [])
            else:
                title = data.get("title") or data.get("name") or "Inconnu"
                genres = [g["name"] for g in data.get("genres", [])]
            genre_str = ", ".join(genres)
            liked_media.append(f"{title} ({genre_str})")
        except Exception as e:
            print(f"[API] Erreur lors de la récupération du média {tmdb_id} : {e}")
    if not liked_media:
        return f"Je n'ai pas de {media_type} à recommander pour le moment."
    if media_type == "game":
        prompt = (
            "Basé sur les jeux vidéo suivants que j'ai aimés :\n"
            + "\n".join(f"- {media}" for media in liked_media)
            + "\n\nRecommande-moi 10 jeux vidéo similaires. "
            + "Ta réponse DOIT être uniquement un tableau JSON contenant les titres. "
            + "Ne fournis aucune explication, introduction ou formatage. "
            + "Exemple de réponse attendue : [\"Jeu A\", \"Jeu B\", \"Jeu C\"]"
        )
    elif media_type == "book":
        prompt = (
            "Basé sur les livres suivants que j'ai aimés :\n"
            + "\n".join(f"- {media}" for media in liked_media)
            + "\n\nRecommande-moi 10 livres similaires. "
            + "Ta réponse DOIT être uniquement un tableau JSON contenant les titres. "
            + "Ne fournis aucune explication, introduction ou formatage. "
            + "Exemple de réponse attendue : [\"Livre A\", \"Livre B\", \"Livre C\"]"
        )
    else:
        prompt = (
            f"Basé sur les {media_type}s suivants que j'ai aimés :\n"
            + "\n".join(f"- {media}" for media in liked_media)
            + f"\n\nRecommande-moi 10 {media_type}s similaires. "
            + "Ta réponse DOIT être uniquement un tableau JSON contenant les titres. "
            + "Ne fournis aucune explication, introduction ou formatage. "
            + "Exemple de réponse attendue : [\"Titre A\", \"Titre B\", \"Titre C\"]"
        )
    return prompt

def build_prompt_from_mood(media_type: str, mood: str) -> str:
    """
    Construit un prompt pour le LLM basé sur une ambiance et un type de média.
    """
    if media_type == "game":
        prompt = (
            f"Je cherche des recommandations de jeux vidéo pour une ambiance '{mood}'. "
            "Propose-moi une liste de 10 jeux vidéo qui correspondent à cette ambiance. "
            "Ta réponse DOIT être uniquement un tableau JSON contenant les titres. "
            "Ne fournis aucune explication, introduction ou formatage. "
            "Exemple de réponse attendue : [\"Jeu A\", \"Jeu B\", \"Jeu C\"]"
        )
    elif media_type == "book":
        prompt = (
            f"Je cherche des recommandations de livres pour une ambiance '{mood}'. "
            "Propose-moi une liste de 10 livres qui correspondent à cette ambiance. "
            "Ta réponse DOIT être uniquement un tableau JSON contenant les titres. "
            "Ne fournis aucune explication, introduction ou formatage. "
            "Exemple de réponse attendue : [\"Livre A\", \"Livre B\", \"Livre C\"]"
        )
    else:
        prompt = (
            f"Je cherche des recommandations de {media_type}s pour une ambiance '{mood}'. "
            f"Propose-moi une liste de 10 {media_type}s qui correspondent à cette ambiance. "
            "Ta réponse DOIT être uniquement un tableau JSON contenant les titres. "
            "Ne fournis aucune explication, introduction ou formatage. "
            "Exemple de réponse attendue : [\"Titre A\", \"Titre B\", \"Titre C\"]"
        )
    return prompt

# Fonctions spécifiques pour compatibilité descendante (films)
def get_top_movies(time_window: str = "day") -> list[dict]:
    return get_top_media("movie", time_window)

def get_movie_info(tmdb_id: str) -> dict:
    return get_media_info("movie", tmdb_id)

def search_movie(title: str) -> Optional[dict]:
    return search_media("movie", title)

def get_recommendations_from_movie(tmdb_id: str) -> list[dict]:
    return get_recommendations_from_media("movie", tmdb_id)

def build_prompt_from_liked_movies(tmdb_ids: list[str]) -> str:
    return build_prompt_from_liked_media("movie", tmdb_ids)

def build_prompt_from_mood_movie(mood: str) -> str:
    return build_prompt_from_mood("movie", mood)
