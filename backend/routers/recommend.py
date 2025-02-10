from core.recommender import (
    fetch_recipe_info,
    get_matching_recipes,
    map_user_input_to_criteria,
)
from fastapi import APIRouter, HTTPException

from backend.models.schemas import RecommendationRequest

router = APIRouter()


@router.post("/recommend")
def recommend_recipes(request: RecommendationRequest):
    criteria = map_user_input_to_criteria(
        cooking_method=request.cooking_method,
        servings_bin=request.servings_bin,
        diet_types=request.diet_types,
        meal_type=request.meal_type,
        cook_time=request.cook_time,
        health_types=request.health_types,
        cuisine_region=request.cuisine_region,
        ingredients=request.ingredients,
        weights=request.weights,
    )
    recipe_ids = get_matching_recipes(
        criteria=criteria, top_k=request.top_k, flexible=request.flexible
    )
    return recipe_ids


@router.get("/recipe/{recipe_id}")
def get_recipe_by_id(recipe_id: str):
    info = fetch_recipe_info(recipe_id)
    print(info)
    if not info:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return info
