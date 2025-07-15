from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..schemas.interaction import LikeRequest, MoodRecommendationRequest
from ..db.mongo import interactions_collection
from ..services.tmdb_client import (
    build_prompt_from_liked_media, search_media, build_prompt_from_mood, get_top_movies, get_top_media
)
from ..services.openrouter_client import query_openrouter
from ..services.auth import get_user_id_from_token
from ..services.rawg_client import get_suggested_games, get_top_games
from ..services.openlibrary_client import get_book_info, search_book
import json
from ..schemas.media import MediaRecommendation, MediaType

router = APIRouter()
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    return get_user_id_from_token(token)

@router.get("/recommendations")
def recommend(
    user_id: str = Depends(get_current_user),
    media_type: str = Query("movie", enum=["movie", "tv", "game", "book"])
):
    record = interactions_collection.find_one({"user_id": user_id})
    liked_ids = record.get("liked_ids", {}) if record else {}
    if isinstance(liked_ids, list):
        liked_ids = {"movie": liked_ids}
    ids = liked_ids.get(media_type, [])
    if not ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Aucun {media_type} aimé trouvé pour cet utilisateur.")
    # --- LOGIQUE SPECIALE POUR LES JEUX ---
    if media_type == "game":
        suggestions = []
        seen_ids = set()
        for game_id in ids:
            try:
                for game in get_suggested_games(game_id, page_size=10):
                    if game["id"] not in seen_ids:
                        suggestions.append(MediaRecommendation.from_game(game))
                        seen_ids.add(game["id"])
            except Exception as e:
                print(f"[RAWG] Erreur suggestion pour {game_id}: {e}")
        # Suggestions LLM (complément)
        if len(suggestions) < 10:
            prompt = build_prompt_from_liked_media(media_type, ids)
            llm_response = query_openrouter(prompt)
            try:
                content_str = llm_response['choices'][0]['message']['content']
                if content_str.strip().startswith("```json"):
                    content_str = content_str.strip()[7:-3].strip()
                elif content_str.strip().startswith("`"):
                    content_str = content_str.strip().strip('`')
                media_titles = json.loads(content_str)
                if isinstance(media_titles, list):
                    for title in media_titles:
                        game = search_media(media_type, title)
                        if game and game["id"] not in seen_ids:
                            suggestions.append(MediaRecommendation.from_game(game))
                            seen_ids.add(game["id"])
                        if len(suggestions) >= 10:
                            break
            except Exception as e:
                print(f"[LLM] Erreur parsing LLM pour jeux: {e}")
        return suggestions[:10]
    # --- LOGIQUE SPECIALE POUR LES LIVRES ---
    if media_type == "book":
        suggestions = []
        seen_olids = set()
        authors = set()
        subjects = set()
        # Récupérer auteurs et genres des livres likés
        for olid in ids:
            try:
                book = get_book_info(olid)
                if "authors" in book:
                    for a in book["authors"]:
                        if "name" in a:
                            authors.add(a["name"])
                if "subjects" in book:
                    for s in book["subjects"]:
                        subjects.add(s)
            except Exception as e:
                print(f"[OpenLibrary] Erreur info livre {olid}: {e}")
        # Suggestions par auteur
        for author in list(authors)[:2]:
            try:
                results = search_book(author)
                for doc in results.get("docs", [])[:5]:
                    olid = doc.get("key", "").replace("/works/", "")
                    if olid and olid not in seen_olids:
                        suggestions.append(MediaRecommendation.from_book(doc))
                        seen_olids.add(olid)
            except Exception as e:
                print(f"[OpenLibrary] Erreur suggestion auteur {author}: {e}")
        # Suggestions par genre
        for subject in list(subjects)[:2]:
            try:
                results = search_book(subject)
                for doc in results.get("docs", [])[:5]:
                    olid = doc.get("key", "").replace("/works/", "")
                    if olid and olid not in seen_olids:
                        suggestions.append(MediaRecommendation.from_book(doc))
                        seen_olids.add(olid)
            except Exception as e:
                print(f"[OpenLibrary] Erreur suggestion genre {subject}: {e}")
        # Suggestions LLM (complément)
        if len(suggestions) < 10:
            prompt = build_prompt_from_liked_media(media_type, ids)
            llm_response = query_openrouter(prompt)
            try:
                content_str = llm_response['choices'][0]['message']['content']
                if content_str.strip().startswith("```json"):
                    content_str = content_str.strip()[7:-3].strip()
                elif content_str.strip().startswith("`"):
                    content_str = content_str.strip().strip('`')
                media_titles = json.loads(content_str)
                if isinstance(media_titles, list):
                    for title in media_titles:
                        doc = search_book(title)
                        if doc and "key" in doc and doc["key"].replace("/works/", "") not in seen_olids:
                            suggestions.append(MediaRecommendation.from_book(doc))
                            seen_olids.add(doc["key"].replace("/works/", ""))
                        if len(suggestions) >= 10:
                            break
            except Exception as e:
                print(f"[LLM] Erreur parsing LLM pour livres: {e}")
        return suggestions[:10]
    # --- LOGIQUE GENERIQUE POUR AUTRES MEDIAS ---
    prompt = build_prompt_from_liked_media(media_type, ids)
    llm_response = query_openrouter(prompt)
    try:
        content_str = llm_response['choices'][0]['message']['content']
        if content_str.strip().startswith("```json"):
            content_str = content_str.strip()[7:-3].strip()
        elif content_str.strip().startswith("`"):
            content_str = content_str.strip().strip('`')
        media_titles = json.loads(content_str)
        if not isinstance(media_titles, list):
            raise ValueError("La réponse de l'IA n'est pas une liste.")
        recommendations = []
        for title in media_titles:
            media_details = search_media(media_type, title)
            if not media_details:
                continue
            if media_type == "book":
                recommendations.append(MediaRecommendation.from_book(media_details))
            else:
                recommendations.append(MediaRecommendation.from_movie_tv(media_details, MediaType(media_type)))
        return recommendations
    except (KeyError, IndexError, ValueError) as e:
        raw_content = llm_response.get('choices', [{}])[0].get('message', {}).get('content', 'Contenu non disponible')
        print(f"Erreur de parsing de la réponse de l'IA: {e}")
        print(f"Réponse brute: {raw_content}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de parser la recommandation de l'IA."
        )

@router.post("/recommendations/mood")
def recommend_by_mood(
    data: MoodRecommendationRequest,
    user_id: str = Depends(get_current_user),
    media_type: str = Query("movie", enum=["movie", "tv", "game", "book"])
):
    prompt = build_prompt_from_mood(media_type, data.mood.value)
    llm_response = query_openrouter(prompt)
    try:
        content_str = llm_response['choices'][0]['message']['content']
        if content_str.strip().startswith("```json"):
            content_str = content_str.strip()[7:-3].strip()
        elif content_str.strip().startswith("`"):
            content_str = content_str.strip().strip('`')
        media_titles = json.loads(content_str)
        if not isinstance(media_titles, list):
            raise ValueError("La réponse de l'IA n'est pas une liste.")
        recommendations = []
        for title in media_titles:
            media_details = search_media(media_type, title)
            if not media_details:
                continue
            if media_type == "game":
                recommendations.append(MediaRecommendation.from_game(media_details))
            elif media_type == "book":
                recommendations.append(MediaRecommendation.from_book(media_details))
            else:
                recommendations.append(MediaRecommendation.from_movie_tv(media_details, MediaType(media_type)))
        return recommendations
    except (KeyError, IndexError, ValueError) as e:
        raw_content = llm_response.get('choices', [{}])[0].get('message', {}).get('content', 'Contenu non disponible')
        print(f"Erreur de parsing de la réponse de l'IA: {e}")
        print(f"Réponse brute: {raw_content}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de parser la recommandation de l'IA."
        )

@router.get("/recommendations/multiple_media")
def recommend_multiple_media(user_id: str = Depends(get_current_user)):
    result = {}
    types = ["movie", "tv", "game", "book"]
    for media_type in types:
        print(f"[multiple_media] Traitement de {media_type}")
        record = interactions_collection.find_one({"user_id": user_id})
        liked_ids = record.get("liked_ids", {}) if record else {}
        if isinstance(liked_ids, list):
            liked_ids = {"movie": liked_ids}
        ids = liked_ids.get(media_type, [])
        print(f"[multiple_media] {media_type} ids :", ids)
        # Fallback si aucun like : top médias
        if not ids:
            if media_type == "movie":
                top = get_top_movies("day")[:3]
                result[media_type] = [MediaRecommendation.from_movie_tv(m, MediaType.MOVIE) for m in top]
            elif media_type == "tv":
                top = get_top_media("tv", "day")[:3]
                result[media_type] = [MediaRecommendation.from_movie_tv(m, MediaType.TV) for m in top]
            elif media_type == "game":
                top = get_top_games(page_size=3)
                result[media_type] = [MediaRecommendation.from_game(g) for g in top]
            elif media_type == "book":
                books = search_book("the").get("docs", [])
                if not books:
                    books = search_book("a").get("docs", [])
                if not books:
                    # Fallback ultime : livres populaires en dur
                    books = [
                        {"title": "1984", "author_name": ["George Orwell"], "key": "/works/OL7343626W"},
                        {"title": "Le Petit Prince", "author_name": ["Antoine de Saint-Exupéry"], "key": "/works/OL262758W"},
                        {"title": "Harry Potter à l'école des sorciers", "author_name": ["J.K. Rowling"], "key": "/works/OL82563W"},
                    ]
                print("[multiple_media] Livres fallback :", books[:3])
                recos = [MediaRecommendation.from_book(b) for b in books[:3]]
                print("[multiple_media] Livres recos :", recos)
                result[media_type] = recos
            continue
        if media_type == "game":
            # LOGIQUE LLM UNIQUEMENT POUR LES JEUX
            prompt = build_prompt_from_liked_media(media_type, ids)
            llm_response = query_openrouter(prompt)
            try:
                content_str = llm_response['choices'][0]['message']['content']
                if content_str.strip().startswith("```json"):
                    content_str = content_str.strip()[7:-3].strip()
                elif content_str.strip().startswith("`"):
                    content_str = content_str.strip().strip('`')
                media_titles = json.loads(content_str)
                if not isinstance(media_titles, list):
                    result[media_type] = []
                    continue
                recommendations = []
                seen_ids = set()
                for title in media_titles:
                    game = search_media(media_type, title)
                    if game and game["id"] not in seen_ids:
                        recommendations.append(MediaRecommendation.from_game(game))
                        seen_ids.add(game["id"])
                    if len(recommendations) >= 3:
                        break
                result[media_type] = recommendations
            except Exception as e:
                print(f"[LLM] Erreur parsing LLM pour jeux: {e}")
                result[media_type] = []
        elif media_type == "book":
            suggestions = []
            seen_olids = set()
            authors = set()
            subjects = set()
            for olid in ids:
                try:
                    book = get_book_info(olid)
                    if "authors" in book:
                        for a in book["authors"]:
                            if "name" in a:
                                authors.add(a["name"])
                    if "subjects" in book:
                        for s in book["subjects"]:
                            subjects.add(s)
                except Exception as e:
                    print(f"[OpenLibrary] Erreur info livre {olid}: {e}")
            print(f"[multiple_media] book authors: {authors}, subjects: {subjects}")
            for author in list(authors)[:1]:
                try:
                    results = search_book(author)
                    for doc in results.get("docs", [])[:3]:
                        olid = doc.get("key", "").replace("/works/", "")
                        if olid and olid not in seen_olids:
                            suggestions.append(MediaRecommendation.from_book(doc))
                            seen_olids.add(olid)
                        if len(suggestions) >= 3:
                            break
                except Exception as e:
                    print(f"[OpenLibrary] Erreur suggestion auteur {author}: {e}")
                if len(suggestions) >= 3:
                    break
            print(f"[multiple_media] book suggestions après auteurs: {suggestions}")
            for subject in list(subjects)[:1]:
                try:
                    results = search_book(subject)
                    for doc in results.get("docs", [])[:3]:
                        olid = doc.get("key", "").replace("/works/", "")
                        if olid and olid not in seen_olids:
                            suggestions.append(MediaRecommendation.from_book(doc))
                            seen_olids.add(olid)
                        if len(suggestions) >= 3:
                            break
                except Exception as e:
                    print(f"[OpenLibrary] Erreur suggestion genre {subject}: {e}")
                if len(suggestions) >= 3:
                    break
            print(f"[multiple_media] book suggestions après genres: {suggestions}")
            print(f"[multiple_media] book suggestions finales: {suggestions}")
            if not suggestions:
                # Fallback si aucune suggestion personnalisée
                try:
                    books = search_book("the").get("docs", [])
                except Exception as e:
                    print("[multiple_media] Erreur OpenLibrary (the) :", e)
                    books = []
                if not books:
                    try:
                        books = search_book("a").get("docs", [])
                    except Exception as e:
                        print("[multiple_media] Erreur OpenLibrary (a) :", e)
                        books = []
                if not books:
                    books = [
                        {"title": "1984", "author_name": ["George Orwell"], "key": "/works/OL7343626W"},
                        {"title": "Le Petit Prince", "author_name": ["Antoine de Saint-Exupéry"], "key": "/works/OL262758W"},
                        {"title": "Harry Potter à l'école des sorciers", "author_name": ["J.K. Rowling"], "key": "/works/OL82563W"},
                    ]
                print("[multiple_media] Fallback livres (likes présents) :", books[:3])
                suggestions = [MediaRecommendation.from_book(b) for b in books[:3]]
            result[media_type] = suggestions[:3]
        else:
            prompt = build_prompt_from_liked_media(media_type, ids)
            llm_response = query_openrouter(prompt)
            try:
                content_str = llm_response['choices'][0]['message']['content']
                if content_str.strip().startswith("```json"):
                    content_str = content_str.strip()[7:-3].strip()
                elif content_str.strip().startswith("`"):
                    content_str = content_str.strip().strip('`')
                media_titles = json.loads(content_str)
                if not isinstance(media_titles, list):
                    result[media_type] = []
                    continue
                recommendations = []
                for title in media_titles:
                    media_details = search_media(media_type, title)
                    if not media_details:
                        continue
                    recommendations.append(MediaRecommendation.from_movie_tv(media_details, MediaType(media_type)))
                    if len(recommendations) >= 3:
                        break
                result[media_type] = recommendations
            except Exception as e:
                print(f"[LLM] Erreur parsing LLM pour {media_type}: {e}")
                result[media_type] = []
    return result

@router.post("/like")
def like_media(data: LikeRequest, user_id: str = Depends(get_current_user)):
    record = interactions_collection.find_one({"user_id": user_id})
    if not record:
        interactions_collection.insert_one({
            "user_id": user_id,
            "liked_ids": {data.media_type: [data.media_id]},
            "disliked_ids": {}
        })
    else:
        liked = record.get("liked_ids", {})
        # Correction : si liked est une liste (ancien format), on la convertit en dict
        if isinstance(liked, list):
            liked = {"movie": liked}
        if data.media_type not in liked:
            liked[data.media_type] = []
        if data.media_id not in liked[data.media_type]:
            liked[data.media_type].append(data.media_id)
            interactions_collection.update_one(
                {"user_id": user_id},
                {"$set": {"liked_ids": liked}}
            )
    return {"message": "Like enregistré"}

@router.post("/dislike")
def dislike_media(data: LikeRequest, user_id: str = Depends(get_current_user)):
    record = interactions_collection.find_one({"user_id": user_id})
    if not record:
        interactions_collection.insert_one({
            "user_id": user_id,
            "liked_ids": {},
            "disliked_ids": {data.media_type: [data.media_id]}
        })
    else:
        disliked = record.get("disliked_ids", {})
        if isinstance(disliked, list):
            disliked = {"movie": disliked}
        if data.media_type not in disliked:
            disliked[data.media_type] = []
        if data.media_id not in disliked[data.media_type]:
            disliked[data.media_type].append(data.media_id)
            interactions_collection.update_one(
                {"user_id": user_id},
                {"$set": {"disliked_ids": disliked}}
            )
    return {"message": "Dislike enregistré"}

@router.post("/unlike")
def unlike_media(data: LikeRequest, user_id: str = Depends(get_current_user)):
    record = interactions_collection.find_one({"user_id": user_id})
    if not record:
        return {"message": "Aucun like trouvé pour cet utilisateur."}
    liked = record.get("liked_ids", {})
    if isinstance(liked, list):
        liked = {"movie": liked}
    if data.media_type in liked and data.media_id in liked[data.media_type]:
        liked[data.media_type].remove(data.media_id)
        interactions_collection.update_one(
            {"user_id": user_id},
            {"$set": {"liked_ids": liked}}
        )
        return {"message": "Like supprimé"}
    return {"message": "Aucun like trouvé pour ce média."}

@router.post("/undislike")
def undislike_media(data: LikeRequest, user_id: str = Depends(get_current_user)):
    record = interactions_collection.find_one({"user_id": user_id})
    if not record:
        return {"message": "Aucun dislike trouvé pour cet utilisateur."}
    disliked = record.get("disliked_ids", {})
    if isinstance(disliked, list):
        disliked = {"movie": disliked}
    if data.media_type in disliked and data.media_id in disliked[data.media_type]:
        disliked[data.media_type].remove(data.media_id)
        interactions_collection.update_one(
            {"user_id": user_id},
            {"$set": {"disliked_ids": disliked}}
        )
        return {"message": "Dislike supprimé"}
    return {"message": "Aucun dislike trouvé pour ce média."}