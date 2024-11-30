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
    ALLOWED_ORIGINS: List[str] = ["*"]  # In production, replace with specific origins
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

settings = Settings() 