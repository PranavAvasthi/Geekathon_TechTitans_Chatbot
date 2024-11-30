from pydantic import BaseModel #type: ignore
from typing import Optional

class RepositoryRequest(BaseModel):
    repo_url: str

class QueryRequest(BaseModel):
    session_id: str
    query: str

class AnalysisResponse(BaseModel):
    message: str
    session_id: Optional[str] = None 