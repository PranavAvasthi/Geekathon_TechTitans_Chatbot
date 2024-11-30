from typing import Dict, Optional
from pathlib import Path
import tempfile
import shutil
import os
from app.services.code_analyzer import CodeAnalyzer
from app.services.repo_handler import RepoHandler

class AnalyzerService:
    def __init__(self):
        self.analyzers: Dict[str, dict] = {}

    async def create_session(self, repo_url: str) -> tuple[str, str]:
        """Create a new analysis session for a repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Initialize handlers
            repo_handler = RepoHandler()
            analyzer = CodeAnalyzer()
            
            # Clone and process repository
            repo_handler.clone_repo(repo_url)
            code_files = repo_handler.get_all_files()
            analyzer.process_code_files(code_files)
            
            # Create session
            session_id = str(hash(repo_url + temp_dir))
            self.analyzers[session_id] = {
                "analyzer": analyzer,
                "temp_dir": temp_dir,
                "repo_handler": repo_handler
            }
            
            return session_id, "✅ Repository loaded successfully! You can now ask questions about the code."
        except Exception as e:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise Exception(f"Failed to create session: {str(e)}")

    async def analyze_code(self, session_id: str, query: str) -> str:
        """Analyze code using the specified session."""
        if session_id not in self.analyzers:
            raise Exception("Session not found. Please load a repository first.")
        
        analyzer = self.analyzers[session_id]["analyzer"]
        response = analyzer.get_code_explanation(query)
        return response or "No response generated"

    async def cleanup_session(self, session_id: str) -> None:
        """Clean up a session and its resources."""
        if session_id not in self.analyzers:
            raise Exception("Session not found")
        
        # Clean up temporary directory
        temp_dir = self.analyzers[session_id]["temp_dir"]
        try:
            # Clean up repo handler
            if "repo_handler" in self.analyzers[session_id]:
                self.analyzers[session_id]["repo_handler"].cleanup()
            # Remove temp directory
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Cleanup error: {str(e)}")
        
        # Remove analyzer instance
        del self.analyzers[session_id]

# Create a global instance
analyzer_service = AnalyzerService() 