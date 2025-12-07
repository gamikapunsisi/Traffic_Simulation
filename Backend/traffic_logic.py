import random
from typing import Dict, Tuple

NODES = ["A","B","C","D","E","F","G","H","T"]
EDGES = [
    ("A","B"),("A","C"),("A","D"),
    ("B","E"),("B","F"),
    ("C","E"),("C","F"),
    ("D","F"),
    ("E","G"),("E","H"),
    ("F","H"),
    ("G","T"),("H","T")
]

MIN_CAPACITY = 5
MAX_CAPACITY = 15

def generate_random_capacity_graph() -> Dict[str, Dict[str,int]]:
    g = {u:{} for u in NODES}
    for u,v in EDGES:
        g[u][v] = random.randint(MIN_CAPACITY, MAX_CAPACITY)
    return g

# Paste your edmonds_karp_with_flows and dinic functions here
