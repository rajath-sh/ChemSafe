from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict

from core.dependencies import require_role
from core.enums import Role
from core.schemas import CurrentUser
from modules.navigation.schemas import GraphSchema, PathRequest, PathResponse, MatrixResponse
from modules.navigation.floyd_warshall import FloydWarshall

router = APIRouter()

@router.post("/compute-matrices", response_model=MatrixResponse)
def compute_matrices(
    graph: GraphSchema,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    fw = FloydWarshall(graph)
    dist, nxt = fw.get_matrices()
    
    # Clean up infinity for JSON serialization
    clean_dist = {}
    for u in dist:
        clean_dist[u] = {}
        for v in dist[u]:
            val = dist[u][v]
            clean_dist[u][v] = -1.0 if val == float('inf') else val
            
    return MatrixResponse(distance_matrix=clean_dist, next_node_matrix=nxt)

@router.post("/shortest-path", response_model=PathResponse)
def get_shortest_path(
    req: PathRequest,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    fw = FloydWarshall(req.graph)
    path, dist = fw.get_shortest_path(req.source_id, req.target_id)
    
    if dist == -1.0:
        raise HTTPException(status_code=404, detail="No path exists between the given nodes.")
        
    return PathResponse(path_nodes=path, total_distance=dist)

@router.post("/dry-run")
def get_dry_run(
    graph: GraphSchema,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    fw = FloydWarshall(graph)
    return {"nodes": graph.nodes, "history": fw.history}
