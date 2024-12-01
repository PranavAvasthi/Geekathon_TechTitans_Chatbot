from pydantic_settings import BaseSettings #type: ignore
from typing import List
import os
from dotenv import load_dotenv #type: ignore

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Code Analysis API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for analyzing code repositories using AI"
    API_V1_STR: str = "/api"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]  # Allow all origins in development
    ALLOWED_METHODS: List[str] = ["*"]  # Allow all methods
    ALLOWED_HEADERS: List[str] = ["*"]  # Allow all headers
    ALLOW_CREDENTIALS: bool = False  # Set to False when using "*" origins
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    class Config:
        case_sensitive = True

settings = Settings() 