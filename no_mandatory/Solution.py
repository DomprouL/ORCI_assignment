from dataclasses import dataclass, field
from typing import List, Set

@dataclass
class Column:
    nodes: list
    profit: float
    cost: float
    visits: set
    
@dataclass
class Route:
    # Sequence of node IDs (always starts and ends with depot = 0)
    nodes: List[int] = field(default_factory=lambda: [0, 0])

    # Total demand served by this route
    load: int = 0

    # Total travel time of this route
    time: float = 0.0

    # Total collected profit
    profit: int = 0


@dataclass
class Solution:
    routes: List[Route]

    visited: Set[int] = field(default_factory=set)

    total_profit: int = 0
    total_time: float = 0.0
    total_load: int = 0

