from pydantic import BaseModel
from typing import List, Optional, Dict


class RecommendationRequest(BaseModel):
    cooking_method: Optional[str] = None
    servings_bin: Optional[str] = None
    diet_types: List[str] = []
    meal_type: List[str] = []
    cook_time: Optional[str] = None
    # health_types will be combined from separate protein and carb selects:
    health_types: List[str] = []
    cuisine_region: Optional[str] = None
    ingredients: List[str] = []
    weights: Dict[str, float] = {}
    top_k: int = 5
    flexible: bool = False


class RecipeInfo(BaseModel):
    name: str
    description: Optional[str] = None
    meal_type: List[str]
    diet_type: List[str]
    health_type: List[str]
    region: List[str]
    country: List[str]
    cook_time: str
    ingredients: List[str]
    instructions: str
    nutrition_facts: Dict[str, str]
    images: List[str]
