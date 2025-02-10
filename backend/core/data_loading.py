# core/data_loading.py

import os
import re
from pathlib import Path

import pandas as pd

RECIPES_DF = Path(os.getenv("RECIPES_DF", "./recipes.csv"))


def load_recipes_df() -> pd.DataFrame:
    if not RECIPES_DF.exists():
        raise RuntimeError(f"Recipes DataFrame not found: {RECIPES_DF}")
    return pd.read_csv(RECIPES_DF)


# Load the DataFrame once
recipes_df = load_recipes_df()


def get_unique_ingredients() -> list:
    """
    Extract unique ingredient strings from the 'BestUsdaIngredientName' column,
    but only split on semicolons. This preserves multi-word USDA names like
    'BLUEBERRIES,RAW' as a single item.
    """
    unique_ings = set()
    if "BestUsdaIngredientName" in recipes_df.columns:
        for ing_str in recipes_df["BestUsdaIngredientName"].dropna().unique():
            # Split only on semicolons
            parts = re.split(r";", str(ing_str))
            for part in parts:
                cleaned = part
                # Skip empty or known placeholders
                if cleaned and cleaned != "unknown" and cleaned != "nan":
                    unique_ings.add(cleaned)

    return sorted(unique_ings)
