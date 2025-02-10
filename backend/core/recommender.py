from typing import Any, Dict, List, Tuple

import pandas as pd
from pykeen.predict import predict_target
from sklearn.preprocessing import MinMaxScaler

from .data_loading import recipes_df
from .graph_triples import map_health_attribute
from .model import model, triples_factory


def map_user_input_to_criteria(
    cooking_method: str | None,
    servings_bin: str | None,
    diet_types: List[str],
    meal_type: List[str],
    cook_time: str | None,
    health_types: List[str],
    cuisine_region: str | None,
    ingredients: List[str],
    weights: Dict[str, float],
) -> List[Tuple[str, str, float]]:
    """
    Convert user input into a list of (tail_entity, relation, weight) triples for prediction.
    For free–text inputs (like cooking_method) we lower–case; for select inputs we use the value as is.
    """
    criteria = []

    if cooking_method:
        cm = cooking_method.strip().lower()  # free–text input
        tail = f"cooking_method_{cm}"
        criteria.append((tail, "usesCookingMethod", weights.get("cooking_method", 1.0)))

    if servings_bin:
        sb = servings_bin.strip()  # from a select; use as is
        tail = f"servings_bin_{sb}"
        criteria.append((tail, "hasServingsBin", weights.get("servings_bin", 1.0)))

    for dt in diet_types:
        dt_clean = dt.strip()  # use as is (e.g. "Standard")
        tail = f"diet_type_{dt_clean}"
        criteria.append((tail, "hasDietType", weights.get("diet_types", 1.0)))

    for mt in meal_type:
        mt_clean = mt.strip()  # use as is (e.g. "dessert")
        tail = f"meal_type_{mt_clean}"
        criteria.append((tail, "isForMealType", weights.get("meal_type", 1.0)))

    if cook_time:
        ct = cook_time.strip()  # use as is (e.g. "less than 60 Mins")
        tail = f"cook_time_{ct}"
        criteria.append((tail, "hasCookTime", weights.get("cook_time", 1.0)))

    for ht in health_types:
        ht_clean = ht.strip()  # these come from separate selects; use as is
        relation = map_health_attribute(ht_clean)
        tail = f"health_attribute_{ht_clean}"
        criteria.append((tail, relation, weights.get("healthy_type", 1.0)))

    if cuisine_region:
        cr = cuisine_region.strip()  # free–text input; use as is
        tail = f"cuisine_region_{cr}"
        criteria.append((tail, "hasCuisineRegion", weights.get("cuisine_region", 1.0)))

    for ing in ingredients:
        ing_clean = ing.strip()  # ingredients from backend are already lower-case
        tail = f"ingredient_{ing_clean}"
        criteria.append((tail, "containsIngredient", weights.get("ingredients", 1.0)))

    return criteria


def _normalize_scores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["normalized_score"] = 0.0
        return df
    scaler = MinMaxScaler()
    df["normalized_score"] = scaler.fit_transform(df[["score"]])
    return df


def get_matching_recipes(
    criteria: List[Tuple[str, str, float]], top_k: int, flexible: bool
) -> List[str]:
    """
    For each (tail, relation, weight) criterion, predict head nodes using PyKEEN,
    merge results (union if flexible, intersection if not), and return the top_k recipe IDs.
    """
    if not criteria:
        return []

    all_preds = []
    for tail, relation, weight in criteria:
        preds = predict_target(
            model=model, relation=relation, tail=tail, triples_factory=triples_factory
        ).df
        preds = _normalize_scores(preds)
        preds["weighted_score"] = preds["normalized_score"] * weight
        preds = preds[["head_label", "weighted_score"]]
        all_preds.append(preds)

    merged = all_preds[0]
    for other in all_preds[1:]:
        if flexible:
            merged = merged.merge(
                other, on="head_label", how="outer", suffixes=("", "_y")
            )
            merged["weighted_score"] = merged["weighted_score"].fillna(0) + merged[
                "weighted_score_y"
            ].fillna(0)
            merged.drop(columns=["weighted_score_y"], inplace=True)
        else:
            merged = merged.merge(
                other, on="head_label", how="inner", suffixes=("", "_y")
            )
            merged["weighted_score"] += merged["weighted_score_y"]
            merged.drop(columns=["weighted_score_y"], inplace=True)

    merged = merged[merged["head_label"].str.startswith("recipe_")]
    merged.sort_values(by="weighted_score", ascending=False, inplace=True)
    merged = merged.head(top_k)

    def parse_recipe_id(node_str: str) -> str:
        return node_str.split("recipe_", 1)[1]

    ids = merged["head_label"].apply(parse_recipe_id).to_list()
    return ids


def fetch_recipe_info(recipe_id: str) -> Dict[str, Any] | None:
    """
    Return recipe details from the recipes DataFrame by recipe_id.
    """
    try:
        rid_int = int(recipe_id)
    except ValueError:
        return None

    row = recipes_df[recipes_df["RecipeId"] == rid_int]
    if row.empty:
        return None
    return row.iloc[0].to_dict()
