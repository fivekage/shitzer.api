import requests

OPENLIBRARY_BASE_URL = "https://openlibrary.org"

def search_book(title: str):
    r = requests.get(f"{OPENLIBRARY_BASE_URL}/search.json", params={"q": title})
    r.raise_for_status()
    results = r.json().get("docs", [])
    if results:
        # On retourne le premier résultat pertinent (OLID)
        doc = results[0]
        doc["olid"] = doc.get("key", "").replace("/works/", "")
        return doc
    return None

def get_book_info(olid: str):
    r = requests.get(f"{OPENLIBRARY_BASE_URL}/works/{olid}.json")
    r.raise_for_status()
    return r.json() 