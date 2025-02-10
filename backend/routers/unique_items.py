from fastapi import APIRouter
from typing import List
from core.data_loading import get_unique_ingredients

router = APIRouter()


@router.get("/unique_ingredients", response_model=List[str])
def get_unique_ingredients_endpoint():
    return get_unique_ingredients()
