from typing import Any, Dict, List, Tuple

import networkx as nx
import numpy as np
import pandas as pd

UNKNOWN_PLACEHOLDER = "unknown"


def map_health_attribute(element: str) -> str:
    """
    Map a healthy attribute string to a specific relation label.
    For example, if the attribute contains “protein” then return “HasProteinLevel”.
    """
    e = element.lower()
    if "protein" in e:
        return "HasProteinLevel"
    elif "carb" in e:
        return "HasCarbLevel"
    elif "fat" in e and "saturated" not in e:
        return "HasFatLevel"
    elif "saturated_fat" in e:
        return "HasSaturatedFatLevel"
    elif "calorie" in e:
        return "HasCalorieLevel"
    elif "sodium" in e:
        return "HasSodiumLevel"
    elif "sugar" in e:
        return "HasSugarLevel"
    elif "fiber" in e:
        return "HasFiberLevel"
    elif "cholesterol" in e:
        return "HasCholesterolLevel"
    else:
        return "HasHealthAttribute"


def split_and_clean(value: str, delimiter: str) -> List[str]:
    """Splits a string by the given delimiter and trims whitespace."""
    return [v.strip() for v in value.split(delimiter) if v.strip()]


def load_recipes_from_dataframe(df: pd.DataFrame) -> Dict[Any, Dict[str, Any]]:
    """
    Extract relevant columns from the DataFrame into a dictionary keyed by RecipeId.
    Retained columns: RecipeId, Cooking_Method, servings_bin, Diet_Types, meal_type,
                      cook_time, Healthy_Type, CuisineRegion, BestUsdaIngredientName.
    """
    columns_to_keep = [
        "RecipeId",
        "Cooking_Method",
        "servings_bin",
        "Diet_Types",
        "meal_type",
        "cook_time",
        "Healthy_Type",
        "CuisineRegion",
        "BestUsdaIngredientName",
    ]
    missing = set(columns_to_keep) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")

    recipes = {}
    for _, row in df.iterrows():
        recipe_id = row["RecipeId"]
        recipe_data = {col: row[col] for col in columns_to_keep}
        recipes[recipe_id] = recipe_data
    return recipes


def create_graph_and_triples(
    recipes: Dict[Any, Dict[str, Any]],
) -> Tuple[nx.DiGraph, np.ndarray]:
    """
    Build a directed knowledge graph (KG) and extract triples.
    Recipe nodes: ("recipe", RecipeId)
    Attributes:
      - Cooking_Method → usesCookingMethod
      - servings_bin   → hasServingsBin
      - cook_time      → hasCookTime
      - CuisineRegion  → hasCuisineRegion
      - Diet_Types     → hasDietType (list; comma–delimited)
      - meal_type      → isForMealType (list; comma–delimited)
      - Healthy_Type   → processed via map_health_attribute
      - BestUsdaIngredientName → containsIngredient (list; semicolon–delimited)
    """
    G = nx.DiGraph()
    triples = []

    # Single–value attributes.
    attribute_mappings = {
        "Cooking_Method": ("usesCookingMethod", "cooking_method"),
        "servings_bin": ("hasServingsBin", "servings_bin"),
        "cook_time": ("hasCookTime", "cook_time"),
        "CuisineRegion": ("hasCuisineRegion", "cuisine_region"),
    }

    # List–based attributes.
    list_attributes = {
        "Diet_Types": ("hasDietType", "diet_type", ","),
        "meal_type": ("isForMealType", "meal_type", ","),
    }

    ingredient_relation = "containsIngredient"
    ingredient_node_type = "ingredient"
    ingredient_delimiter = ";"  # semicolon–delimited

    for recipe_id, details in recipes.items():
        # Create the recipe node.
        recipe_node = ("recipe", recipe_id)
        G.add_node(recipe_node, type="recipe", RecipeId=recipe_id)

        # Process single–value attributes.
        for col, (relation, node_type) in attribute_mappings.items():
            element = details.get(col, None)
            if (
                element
                and element != UNKNOWN_PLACEHOLDER
                and str(element).strip() != ""
            ):
                element_clean = str(element).strip()  # Preserve original casing!
                node_id = (node_type, element_clean)
                if not G.has_node(node_id):
                    G.add_node(node_id, type=node_type, label=element_clean)
                G.add_edge(recipe_node, node_id, relation=relation)
                triples.append((str(recipe_node), relation, str(node_id)))

        # Process Healthy_Type.
        healthy = details.get("Healthy_Type", None)
        if healthy and healthy != UNKNOWN_PLACEHOLDER and str(healthy).strip() != "":
            healthy_elements = split_and_clean(str(healthy), ",")
            for element in healthy_elements:
                if element:
                    relation = map_health_attribute(element)
                    node_id = ("health_attribute", element)
                    if not G.has_node(node_id):
                        G.add_node(node_id, type="health_attribute", label=element)
                    G.add_edge(recipe_node, node_id, relation=relation)
                    triples.append((str(recipe_node), relation, str(node_id)))

        # Process list–based attributes.
        for col, (relation, node_type, delimiter) in list_attributes.items():
            value = details.get(col, None)
            if value and value != UNKNOWN_PLACEHOLDER and str(value).strip() != "":
                elements = split_and_clean(str(value), delimiter)
                for element in elements:
                    if element:
                        node_id = (node_type, element)
                        if not G.has_node(node_id):
                            G.add_node(node_id, type=node_type, label=element)
                        G.add_edge(recipe_node, node_id, relation=relation)
                        triples.append((str(recipe_node), relation, str(node_id)))

        # Process ingredients.
        best_usda = details.get("BestUsdaIngredientName", None)
        if (
            best_usda
            and best_usda != UNKNOWN_PLACEHOLDER
            and str(best_usda).strip() != ""
        ):
            ingredients = split_and_clean(str(best_usda), ingredient_delimiter)
            for ingredient in ingredients:
                if ingredient:
                    node_id = (
                        "ingredient",
                        ingredient.lower(),
                    )  # ingredients stored in lower-case
                    if not G.has_node(node_id):
                        G.add_node(node_id, type=ingredient_node_type, label=ingredient)
                    G.add_edge(recipe_node, node_id, relation=ingredient_relation)
                    triples.append(
                        (str(recipe_node), ingredient_relation, str(node_id))
                    )

    triples_array = np.array(triples, dtype=str)
    return G, triples_array


def save_triples(triples_array: np.ndarray, file_path: str) -> None:
    df = pd.DataFrame(triples_array, columns=["Head", "Relation", "Tail"])
    df.to_csv(file_path, index=False)


def save_graph(G: nx.DiGraph, file_path: str) -> None:
    with open(file_path, "wb") as f:
        import pickle

        pickle.dump(G, f)
