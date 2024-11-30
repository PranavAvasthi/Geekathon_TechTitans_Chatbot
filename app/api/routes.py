from fastapi import APIRouter, HTTPException #type: ignore
from app.models.requests import RepositoryRequest, QueryRequest, AnalysisResponse
from app.services.analyzer import analyzer_service

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Code Analysis API"}

@router.post("/repository", response_model=AnalysisResponse)
async def load_repository(request: RepositoryRequest):
    """Load and analyze a repository."""
    try:
        session_id, message = await analyzer_service.create_session(request.repo_url)
        return AnalysisResponse(message=message, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_code(request: QueryRequest):
    """Analyze code using an existing session."""
    try:
        response = await analyzer_service.analyze_code(request.session_id, request.query)
        return AnalysisResponse(message=response)
    except Exception as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up a session and its resources."""
    try:
        await analyzer_service.cleanup_session(session_id)
        return {"message": "Session cleaned up successfully"}
    except Exception as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e)) 