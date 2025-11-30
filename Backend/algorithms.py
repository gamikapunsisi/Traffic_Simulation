"""
Maximum Flow Algorithms
Implements Edmonds-Karp and Dinic's algorithms
"""
import random
from typing import Dict, Tuple

# Graph topology
NODES = ["A", "B", "C", "D", "E", "F", "G", "H", "T"]
EDGES = [
    ("A", "B"), ("A", "C"), ("A", "D"),
    ("B", "E"), ("B", "F"),
    ("C", "E"), ("C", "F"),
    ("D", "F"),
    ("E", "G"), ("E", "H"),
    ("F", "H"),
    ("G", "T"), ("H", "T")
]

# Constants
MIN_CAPACITY = 5
MAX_CAPACITY = 15


def generate_random_capacity_graph() -> Dict[str, Dict[str, int]]:
    """Generate a random capacity graph"""
    g = {u: {} for u in NODES}
    for u, v in EDGES:
        capacity = random.randint(MIN_CAPACITY, MAX_CAPACITY)
        g[u][v] = capacity
    return g


def edmonds_karp_with_flows(graph: Dict, source: str, sink: str) -> Tuple[int, Dict]:
    """
    Edmonds-Karp algorithm returning max flow and flow dictionary
    
    Args:
        graph: Adjacency list with capacities
        source: Source node
        sink: Sink node
    
    Returns:
        Tuple of (max_flow, flow_dict) where flow_dict maps (u,v) -> flow
    """
    # Create residual graph
    residual = {u: dict(neighbors) for u, neighbors in graph.items()}
    flow_dict = {}
    
    # Initialize flow dictionary
    for u in graph:
        for v in graph[u]:
            flow_dict[(u, v)] = 0
    
    def bfs_find_path():
        """BFS to find augmenting path"""
        queue = [(source, [source])]
        visited = {source}
        
        while queue:
            node, path = queue.pop(0)
            
            if node == sink:
                return path
            
            if node in residual:
                for neighbor, capacity in residual[node].items():
                    if neighbor not in visited and capacity > 0:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        
        return None
    
    max_flow = 0
    
    while True:
        path = bfs_find_path()
        if not path:
            break
        
        # Find minimum capacity along path
        flow = float('inf')
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            flow = min(flow, residual[u][v])
        
        # Update residual graph and flow
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            residual[u][v] -= flow
            if v not in residual:
                residual[v] = {}
            residual[v][u] = residual[v].get(u, 0) + flow
            
            # Track actual flow on original edges
            if (u, v) in flow_dict:
                flow_dict[(u, v)] += flow
        
        max_flow += flow
    
    return max_flow, flow_dict


def dinic(graph: Dict, source: str, sink: str) -> int:
    """
    Dinic's algorithm for max flow
    
    Args:
        graph: Adjacency list with capacities
        source: Source node
        sink: Sink node
    
    Returns:
        Maximum flow value
    """
    # Create residual graph
    residual = {u: dict(neighbors) for u, neighbors in graph.items()}
    
    def bfs_level():
        """Build level graph using BFS"""
        level = {source: 0}
        queue = [source]
        
        while queue:
            u = queue.pop(0)
            
            if u in residual:
                for v, cap in residual[u].items():
                    if v not in level and cap > 0:
                        level[v] = level[u] + 1
                        queue.append(v)
        
        return level if sink in level else None
    
    def dfs_flow(u, pushed, level, start):
        """Send flow using DFS"""
        if u == sink:
            return pushed
        
        if u not in residual:
            return 0
        
        while start[u] < len(list(residual[u].keys())):
            neighbors = list(residual[u].keys())
            if start[u] >= len(neighbors):
                break
                
            v = neighbors[start[u]]
            cap = residual[u][v]
            
            if v in level and level[v] == level[u] + 1 and cap > 0:
                flow = dfs_flow(v, min(pushed, cap), level, start)
                
                if flow > 0:
                    residual[u][v] -= flow
                    if v not in residual:
                        residual[v] = {}
                    residual[v][u] = residual[v].get(u, 0) + flow
                    return flow
            
            start[u] += 1
        
        return 0
    
    max_flow = 0
    
    while True:
        level = bfs_level()
        if not level:
            break
        
        start = {node: 0 for node in graph}
        
        while True:
            flow = dfs_flow(source, float('inf'), level, start)
            if flow == 0:
                break
            max_flow += flow
    
    return max_flow