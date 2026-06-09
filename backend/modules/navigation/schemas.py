from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class NodeSchema(BaseModel):
    id: str
    name: str
    type: str # "sensor" or "transit"
    location: Optional[str] = None

class EdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    weight: float

class GraphSchema(BaseModel):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]

class PathRequest(BaseModel):
    graph: GraphSchema
    source_id: str
    target_id: str

class PathResponse(BaseModel):
    path_nodes: List[str] # List of node IDs in order
    total_distance: float

class MatrixResponse(BaseModel):
    distance_matrix: Dict[str, Dict[str, float]]
    next_node_matrix: Dict[str, Dict[str, Optional[str]]]
