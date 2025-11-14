#!/usr/bin/env python3
"""
Two independent max-flow implementations:
- edmonds_karp(graph, s, t): BFS augmenting path (returns max flow)
- edmonds_karp_with_flows(graph, s, t): returns (max_flow, flow_dict)
Graph format:
graph: dict: {u: {v: capacity, ...}, ...}
"""
import collections

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
    res = _build_residual(graph)
    flow = 0
    while True:
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
            break
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
    return int(flow)

def edmonds_karp_with_flows(graph, s, t):
    """
    Runs Edmonds-Karp and returns (max_flow, flow_dict)
    flow_dict maps (u,v) for original edges to the flow sent (integer).
    """
    # Work on a residual copy
    res = _build_residual(graph)
    flow = 0
    while True:
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
            break
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

    # compute flow on each original edge as original_cap - residual_cap
    flow_dict = {}
    for u in graph:
        for v, orig_cap in graph[u].items():
            residual_cap = res.get(u, {}).get(v, 0)
            sent = orig_cap - residual_cap
            # ensure integer
            flow_dict[(u, v)] = int(sent) if sent >= 0 else 0
    return int(flow), flow_dict

# keep dinic function unchanged (returns flow only)
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
        if 'flow' not in locals():
            flow = 0
        flow += pushed
        if pushed == 0:
            break
    return int(locals().get('flow', 0))