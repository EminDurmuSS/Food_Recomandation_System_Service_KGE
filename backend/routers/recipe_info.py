from fastapi import APIRouter, HTTPException
from models.schemas import RecipeInfo
from core.recommender import fetch_recipe_info

router = APIRouter()


@router.get("/recipe/{recipe_name}", response_model=RecipeInfo)
def get_recipe_info(recipe_name: str):
    info_dict = fetch_recipe_info(recipe_name)
    print(info_dict)
    if info_dict is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RecipeInfo(**info_dict)
