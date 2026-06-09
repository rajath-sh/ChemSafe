from pydantic import BaseModel
from typing import Dict, List

class ClassifierRequest(BaseModel):
    sensor_data: Dict[str, float]

class ClassifierResponse(BaseModel):
    classification: str
    path_taken: List[str]
