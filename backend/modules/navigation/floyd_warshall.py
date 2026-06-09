from typing import List, Dict, Tuple
from modules.navigation.schemas import GraphSchema

class FloydWarshall:
    def __init__(self, graph_data: GraphSchema):
        self.nodes = graph_data.nodes
        self.edges = graph_data.edges
        self.node_ids = [n.id for n in self.nodes]
        self.dist = {}
        self.nxt = {}
        self.history = []
        self._initialize_matrices()
        self._compute()

    def _initialize_matrices(self):
        # Initialize distances to infinity and next node to None
        for u in self.node_ids:
            self.dist[u] = {}
            self.nxt[u] = {}
            for v in self.node_ids:
                if u == v:
                    self.dist[u][v] = 0.0
                    self.nxt[u][v] = v
                else:
                    self.dist[u][v] = float('inf')
                    self.nxt[u][v] = None

        # Populate with edge weights
        # Assuming undirected graph for navigation
        for edge in self.edges:
            u, v, w = edge.source, edge.target, edge.weight
            if u in self.dist and v in self.dist[u]:
                # If there are multiple edges, keep the minimum weight
                if w < self.dist[u][v]:
                    self.dist[u][v] = w
                    self.nxt[u][v] = v
                    self.dist[v][u] = w
                    self.nxt[v][u] = u

    def _compute(self):
        self._record_state("Initial State")
        # Standard Floyd-Warshall O(V^3)
        for k in self.node_ids:
            for i in self.node_ids:
                for j in self.node_ids:
                    if self.dist[i][k] < float('inf') and self.dist[k][j] < float('inf'):
                        new_dist = self.dist[i][k] + self.dist[k][j]
                        if new_dist < self.dist[i][j]:
                            self.dist[i][j] = new_dist
                            self.nxt[i][j] = self.nxt[i][k]
            self._record_state(f"After passing through: {self._get_node_name(k)}")

    def _get_node_name(self, n_id):
        for n in self.nodes:
            if n.id == n_id:
                return n.name
        return n_id

    def _record_state(self, step_name):
        state_dist = {}
        for u in self.dist:
            state_dist[u] = {}
            for v in self.dist[u]:
                val = self.dist[u][v]
                state_dist[u][v] = -1.0 if val == float('inf') else val
        self.history.append({"step": step_name, "matrix": state_dist})

    def get_matrices(self) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, str]]]:
        # Convert infinities to something serializable like -1 for JSON if needed, 
        # or handle in router. Here we leave as float('inf') but will clean in router.
        return self.dist, self.nxt

    def get_shortest_path(self, source: str, target: str) -> Tuple[List[str], float]:
        if source not in self.node_ids or target not in self.node_ids:
            return [], -1.0
            
        if self.dist[source][target] == float('inf'):
            return [], -1.0
            
        path = [source]
        curr = source
        while curr != target:
            curr = self.nxt[curr][target]
            path.append(curr)
            
        return path, self.dist[source][target]
