from pathlib import Path
from typing import List
import tempfile
import shutil
import os
import git #type: ignore

class RepoHandler:
    def __init__(self):
        """Initialize the repository handler."""
        self.repo_path = None
        self.temp_dir = None

    def clone_repo(self, repo_url: str) -> Path:
        """Clone a repository and return its path."""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp()
            
            # Clone repository
            git.Repo.clone_from(repo_url, self.temp_dir)
            self.repo_path = Path(self.temp_dir)
            
            return self.repo_path
        except Exception as e:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            raise Exception(f"Failed to clone repository: {str(e)}")

    def get_all_files(self) -> List[Path]:
        """Get all code files from the repository."""
        if not self.repo_path:
            raise Exception("No repository loaded")
        
        code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c',
            '.h', '.hpp', '.cs', '.go', '.rs', '.swift', '.kt', '.rb',
            '.php', '.html', '.css', '.scss', '.sass', '.less', '.vue',
            '.json', '.yaml', '.yml', '.md', '.sql', '.sh', '.bash',
            '.ps1', '.r', '.m', '.mm', '.f90', '.f95', '.f03', '.f08'
        }
        
        files = []
        for file_path in self.repo_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in code_extensions:
                # Skip common directories to ignore
                if any(part.startswith('.') or part in {'node_modules', 'venv', 'env', 'build', 'dist', 'target'}
                      for part in file_path.parts):
                    continue
                files.append(file_path)
        
        return files

    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Error cleaning up repository: {str(e)}")
            finally:
                self.temp_dir = None
                self.repo_path = None 