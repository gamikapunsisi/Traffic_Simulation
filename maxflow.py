"""
Two independent max-flow implementations:
- edmonds_karp(graph, s, t): BFS augmenting path
- dinic(graph, s, t): Dinic's algorithm with level graph + blocking flow

Graph format used in both functions:
graph: dict: {u: {v: capacity, ...}, ...}
Nodes are strings (e.g., "A", "B", ...)
Both functions DO NOT modify the input graph (they work on internal copies).
"""
import collections
import copy

def _build_residual(graph):
    # Build residual adjacency with reverse edges initialized to 0
    res = {}
    for u in graph:
        res.setdefault(u, {})
        for v,cap in graph[u].items():
            res[u][v] = cap
            res.setdefault(v, {})
            if u not in res[v]:
                res[v][u] = 0
    return res

def edmonds_karp(graph, s, t):
    # Work on a copy of the graph
    res = _build_residual(graph)
    flow = 0
    while True:
        # BFS to find shortest augmenting path
        parent = {s: None}
        q = collections.deque([s])
        while q:
            u = q.popleft()
            for v,cap in res[u].items():
                if cap > 0 and v not in parent:
                    parent[v] = u
                    if v == t:
                        break
                    q.append(v)
            if t in parent:
                break
        if t not in parent:
            break  # no augmenting path
        # find bottleneck
        v = t
        bottleneck = float('inf')
        while v != s:
            u = parent[v]
            bottleneck = min(bottleneck, res[u][v])
            v = u
        # apply
        v = t
        while v != s:
            u = parent[v]
            res[u][v] -= bottleneck
            res[v][u] += bottleneck
            v = u
        flow += bottleneck
    return flow

def dinic(graph, s, t):
    res = _build_residual(graph)
    INF = 10**9

    def bfs_level():
        level = {s: 0}
        q = collections.deque([s])
        while q:
            u = q.popleft()
            for v,cap in res[u].items():
                if cap > 0 and v not in level:
                    level[v] = level[u] + 1
                    q.append(v)
        return level if t in level else None

    def dfs(u, f, t, level, it):
        if u == t:
            return f
        for i in range(it[u], len(adj[u])):
            v = adj[u][i]
            if res[u][v] > 0 and level.get(v, -1) == level[u] + 1:
                pushed = dfs(v, min(f, res[u][v]), t, level, it)
                if pushed:
                    res[u][v] -= pushed
                    res[v][u] += pushed
                    return pushed
            it[u] += 1
        return 0

    # Prebuild adjacency lists for iteration order
    while True:
        level = bfs_level()
        if not level:
            break
        adj = {u: list(res[u].keys()) for u in res}
        it = {u:0 for u in res}
        pushed = 0
        while True:
            f = dfs(s, INF, t, level, it)
            if not f:
                break
            pushed += f
        if pushed == 0:
            break
        # continue until no more level graphs
        # accumulate pushed in flow variable
        # we need to count total pushed across level graphs
        # We'll simply add pushed and continue
        # But make sure next iteration recomputes level graph
        # We'll accumulate to flow outside
        # To make simpler, do a separate accumulation:
        # Instead, accumulate flow per outer loop
        # (we already have pushed)
        # To follow structure, we will add to flow and continue
        # But we need flow variable outside; so modify:
        if 'flow' not in locals():
            flow = 0
        flow += pushed
        # Continue; outer while re-evaluates level graph
    return locals().get('flow', 0)