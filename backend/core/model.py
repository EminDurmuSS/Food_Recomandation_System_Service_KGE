import ast
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from pykeen.models import Model
from pykeen.triples import TriplesFactory

MODEL_PATH = Path(os.getenv("MODEL_PATH", "./model.pkl"))
TRIPLES_PATH = Path(os.getenv("TRIPLES_PATH", "./triples.csv"))


def tuple_to_canonical(s: str) -> str:
    """
    Convert a string like "('meal_type', 'dinner')" to "meal_type_dinner".
    Used when loading the CSV of triples.
    """
    try:
        t = ast.literal_eval(s)  # e.g. ("meal_type", "dinner")
        # Then join with underscore => "meal_type_dinner"
        return f"{t[0]}_{t[1]}"
    except Exception as e:
        print(f"Error converting tuple: {str(e)} => {s}")
        return s


def load_kge_model() -> Model:
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model file not found: {MODEL_PATH}")

    return torch.load(
        MODEL_PATH,
        map_location=torch.device("cpu"),
        weights_only=False,
    )


def get_triples_factory():
    if not TRIPLES_PATH.exists():
        raise RuntimeError(f"Triples file not found: {TRIPLES_PATH}")
    df = pd.read_csv(TRIPLES_PATH)

    # Convert each Head, Relation, Tail string to canonical form
    # so that PyKEEN sees them as consistent strings
    triples = []
    for h, r, t in df[["Head", "Relation", "Tail"]].values:
        ch = tuple_to_canonical(h)
        cr = r.strip()
        ct = tuple_to_canonical(t)
        triples.append((ch, cr, ct))

    return TriplesFactory.from_labeled_triples(
        triples=np.array(triples, dtype=str), create_inverse_triples=False
    )


# Load model and triples factory exactly once:
model = load_kge_model().eval()
triples_factory = get_triples_factory()
