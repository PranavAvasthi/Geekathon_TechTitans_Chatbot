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
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",    # Vite default
        "http://127.0.0.1:5173",    # Vite alternative
        "http://localhost:3000",    # React default
        "http://127.0.0.1:3000",    # React alternative
        "https://geekathon-techtitans-chatbot.onrender.com",  # Backend URL
        "https://geekathon-techtitans-frontend.onrender.com"  # Frontend URL
    ]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = [
        "Content-Type",
        "Authorization",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers"
    ]
    ALLOW_CREDENTIALS: bool = True
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    class Config:
        case_sensitive = True

settings = Settings() 