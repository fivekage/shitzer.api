from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..schemas.interaction import LikeRequest, MoodRecommendationRequest
from ..db.mongo import interactions_collection
from ..services.tmdb_client import build_prompt_from_liked_movies, search_movie, build_prompt_from_mood
from ..services.openrouter_client import query_openrouter
from ..services.auth import get_user_id_from_token
import json

router = APIRouter()
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    return get_user_id_from_token(token)

@router.get("/recommendations")
def recommend(user_id: str = Depends(get_current_user)):
    record = interactions_collection.find_one({"user_id": user_id})
    if not record or not record.get("liked_ids"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucun film aimé trouvé pour cet utilisateur.")

    liked_ids = record.get("liked_ids", [])
    prompt = build_prompt_from_liked_movies(liked_ids)
    llm_response = query_openrouter(prompt)

    try:
        content_str = llm_response['choices'][0]['message']['content']
        
        if content_str.strip().startswith("```json"):
            content_str = content_str.strip()[7:-3].strip()
        elif content_str.strip().startswith("`"):
            content_str = content_str.strip().strip('`')

        movie_titles = json.loads(content_str)
        
        if not isinstance(movie_titles, list):
             raise ValueError("La réponse de l'IA n'est pas une liste.")

        recommendations = []
        for title in movie_titles:
            movie_details = search_movie(title)
            if movie_details:
                recommendations.append({
                    "title": movie_details.get("title"),
                    "id": movie_details.get("id")
                })
        
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
def recommend_by_mood(data: MoodRecommendationRequest, user_id: str = Depends(get_current_user)):
    prompt = build_prompt_from_mood(data.mood.value)
    llm_response = query_openrouter(prompt)

    try:
        content_str = llm_response['choices'][0]['message']['content']
        
        if content_str.strip().startswith("```json"):
            content_str = content_str.strip()[7:-3].strip()
        elif content_str.strip().startswith("`"):
            content_str = content_str.strip().strip('`')

        movie_titles = json.loads(content_str)
        
        if not isinstance(movie_titles, list):
             raise ValueError("La réponse de l'IA n'est pas une liste.")

        recommendations = []
        for title in movie_titles:
            movie_details = search_movie(title)
            if movie_details:
                poster_path = movie_details.get("poster_path")
                recommendations.append({
                    "title": movie_details.get("title"),
                    "id": movie_details.get("id"),
                    "overview": movie_details.get("overview"),
                    "poster_path": poster_path,
                    "release_date": movie_details.get("release_date")
                })
        
        return recommendations
    except (KeyError, IndexError, ValueError) as e:
        raw_content = llm_response.get('choices', [{}])[0].get('message', {}).get('content', 'Contenu non disponible')
        print(f"Erreur de parsing de la réponse de l'IA: {e}")
        print(f"Réponse brute: {raw_content}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de parser la recommandation de l'IA."
        )

@router.post("/like")
def like_movie(data: LikeRequest, user_id: str = Depends(get_current_user)):
    record = interactions_collection.find_one({"user_id": user_id})
    if not record:
        interactions_collection.insert_one({
            "user_id": user_id,
            "liked_ids": [data.movie_id]
        })
    else:
        if data.movie_id not in record.get("liked_ids", []):
            interactions_collection.update_one(
                {"user_id": user_id},
                {"$push": {"liked_ids": data.movie_id}}
            )
    return {"message": "Like enregistré"}


@router.post("/dislike")
def dislike_movie(data: LikeRequest, user_id: str = Depends(get_current_user)):
    record = interactions_collection.find_one({"user_id": user_id})
    if not record:
        interactions_collection.insert_one({
            "user_id": user_id,
            "disliked_ids": [data.movie_id]
        })
    else:
        interactions_collection.update_one(
            {"user_id": user_id},
            {"$push": {"disliked_ids": data.movie_id}}
        )
    return {"message": "Dislike enregistré"}

@router.post("/unlike")
def unlike_movie(data: LikeRequest, user_id: str = Depends(get_current_user)):
    record = interactions_collection.find_one({"user_id": user_id})
    if not record:
        return {"message": "Aucun like trouvé pour cet utilisateur."}
    interactions_collection.update_one(
        {"user_id": user_id},
        {"$pull": {"liked_ids": data.movie_id}}
    )
    return {"message": "Like supprimé"}

@router.post("/undislike")
def unlike_movie(data: LikeRequest, user_id: str = Depends(get_current_user)):
    record = interactions_collection.find_one({"user_id": user_id})
    if not record:
        return {"message": "Aucun dislike trouvé pour cet utilisateur."}
    interactions_collection.update_one(
        {"user_id": user_id},
        {"$pull": {"disliked_ids": data.movie_id}}
    )
    return {"message": "Dislike supprimé"}