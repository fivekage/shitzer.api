from fastapi import APIRouter
from ..schemas.interaction import RecommendationRequest
from ..db.mongo import interactions_collection
from ..services.tmdb_client import build_prompt_from_liked_movies
from ..services.openrouter_client import query_openrouter

router = APIRouter()

@router.post("/recommendations")
def recommend(data: RecommendationRequest):
    record = interactions_collection.find_one({"user_id": data.user_id})
    if not record:
        return {"message": "Aucune interaction enregistrée"}

    liked_ids = record.get("liked_ids", [])
    prompt = build_prompt_from_liked_movies(liked_ids)
    response = query_openrouter(prompt)
    return response
