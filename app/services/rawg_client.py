import requests
from ..config import RAWG_API_KEY

RAWG_BASE_URL = "https://api.rawg.io/api"

def search_game(title: str):
    params = {"key": RAWG_API_KEY, "search": title}
    r = requests.get(f"{RAWG_BASE_URL}/games", params=params)
    r.raise_for_status()
    results = r.json().get("results", [])
    if results:
        return results[0]  # Premier résultat pertinent
    return None

def get_game_info(game_id: int):
    params = {"key": RAWG_API_KEY}
    r = requests.get(f"{RAWG_BASE_URL}/games/{game_id}", params=params)
    r.raise_for_status()
    return r.json()

def get_top_games(year: int = None, ordering: str = "-added", page_size: int = 10):
    """
    Récupère les jeux les plus populaires d'une année donnée (par défaut année en cours), triés par popularité (ajouts utilisateurs).
    """
    import datetime
    if year is None:
        year = datetime.datetime.now().year
    params = {
        "key": RAWG_API_KEY,
        "dates": f"{year}-01-01,{year}-12-31",
        "ordering": ordering,
        "page_size": page_size
    }
    url = f"{RAWG_BASE_URL}/games"
    print(f"[RAWG] get_top_games URL: {url} params: {params}")
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json().get("results", [])

def get_suggested_games(game_id: int, page_size: int = 10):
    """
    Récupère les jeux similaires à un jeu donné via RAWG.
    """
    params = {"key": RAWG_API_KEY, "page_size": page_size}
    url = f"{RAWG_BASE_URL}/games/{game_id}/suggested"
    print(f"[RAWG] get_suggested_games URL: {url} params: {params}")
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json().get("results", []) 