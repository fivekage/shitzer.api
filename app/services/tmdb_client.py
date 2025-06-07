import requests
from typing import Optional
from ..config import TMDB_API_KEY

TMDB_BASE_URL = "https://api.themoviedb.org/3"

def get_top_movies(time_window: str = "day") -> list[dict]:
    """
    Récupère les films les plus populaires.
    """
    url = f"{TMDB_BASE_URL}/trending/movie/{time_window}"

    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR",
        "page": 1
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("results", [])

def get_movie_info(tmdb_id: str) -> dict:
    """
    Récupère les informations détaillées d'un film à partir de son ID TMDB.
    """
    url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "fr-FR"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def search_movie(title: str) -> Optional[dict]:
    """
    Recherche un film par son titre et retourne le premier résultat.
    """
    url = f"{TMDB_BASE_URL}/search/movie"
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


def build_prompt_from_liked_movies(tmdb_ids: list[str]) -> str:
    """
    Construit un prompt textuel basé sur les films likés pour le LLM.
    """
    liked_movies = []

    for tmdb_id in tmdb_ids:
        try:
            data = get_movie_info(tmdb_id)
            title = data.get("title", "Inconnu")
            genres = [g["name"] for g in data.get("genres", [])]
            genre_str = ", ".join(genres)
            liked_movies.append(f"{title} ({genre_str})")
        except requests.RequestException as e:
            print(f"[TMDB] Erreur lors de la récupération du film {tmdb_id} : {e}")

    if not liked_movies:
        return "Je n'ai pas de films à recommander pour le moment."

    prompt = (
        "Basé sur les films suivants que j'ai aimés :\n"
        + "\n".join(f"- {movie}" for movie in liked_movies)
        + "\n\nRecommande-moi 10 films similaires. "
        + "Ta réponse DOIT être uniquement un tableau JSON contenant les titres des films. "
        + "Ne fournis aucune explication, introduction ou formatage. "
        + "Exemple de réponse attendue : [\"Film A\", \"Film B\", \"Film C\"]"
    )
    return prompt

def build_prompt_from_mood(mood: str) -> str:
    """
    Construit un prompt pour le LLM basé sur une ambiance.
    """
    prompt = (
        f"Je cherche des recommandations de films pour une ambiance '{mood}'. "
        "Propose-moi une liste de 10 films qui correspondent à cette ambiance. "
        "Ta réponse DOIT être uniquement un tableau JSON contenant les titres des films. "
        "Ne fournis aucune explication, introduction ou formatage. "
        "Exemple de réponse attendue : [\"Film A\", \"Film B\", \"Film C\"]"
    )
    return prompt
