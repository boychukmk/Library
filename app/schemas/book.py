from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.author import AuthorResponse
from app.core.config import settings


class BookBase(BaseModel):
    title: str
    genre: str
    published_year: int = Field(..., ge=1800, le=2025)

    @classmethod
    def validate_genre(cls, genre: str):
        if genre not in settings.SUPPORTED_GENRES:
            raise ValueError(f"Invalid genre: {genre}. Supported genres: {', '.join(settings.SUPPORTED_GENRES)}")


class BookCreate(BookBase):
    author: str

    def __init__(self, **data):
        super().__init__(**data)
        self.validate_genre(self.genre)


class BookUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    published_year: Optional[int] = Field(None, ge=1800, le=2025)
    author: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.genre:
            BookBase.validate_genre(self.genre)


class BookResponse(BookBase):
    id: int
    author: AuthorResponse

    class Config:
        from_attributes = True
