import os
from typing import ClassVar, List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL must be set")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    PAGE_SIZE: int = 10
    SUPPORTED_GENRES: ClassVar[List[str]] = [
        "Fiction", "Non-Fiction", "Science", "History", "Mystery", "Fantasy"
    ]

    class Config:
        case_sensitive = True


settings = Settings()
