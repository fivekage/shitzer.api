import requests
from ..config import TMDB_API_KEY

TMDB_BASE_URL = "https://api.themoviedb.org/3"

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
        "Voici les films que j'ai aimés :\n"
        + "\n".join(f"- {movie}" for movie in liked_movies)
        + "\nPeux-tu me recommander d'autres films dans le même style ?"
    )
    return prompt
