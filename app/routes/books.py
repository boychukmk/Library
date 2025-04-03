from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.core.permissions import Permissions
from app.crud.raw_sql_crud import (
    create_book, update_book, get_books, get_book_by_id, delete_book, bulk_import_books
)
from app.schemas.book import BookCreate, BookUpdate, BookResponse

router = APIRouter()


@router.post("/", response_model=BookResponse)
async def add_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(Permissions.is_authenticated)
):
    return await create_book(db, book)


@router.get("/{book_id}", response_model=BookResponse)
async def fetch_book(book_id: int, db: AsyncSession = Depends(get_db)):
    return await get_book_by_id(db, book_id)


@router.put("/{book_id}", response_model=BookResponse)
async def modify_book(
    book_id: int,
    book: BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(Permissions.is_authenticated)
):
    return await update_book(db, book_id, book)


@router.delete("/{book_id}")
async def remove_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(Permissions.is_authenticated)
):
    return await delete_book(db, book_id)


@router.get("/", response_model=List[BookResponse])
async def list_books(
        db: AsyncSession = Depends(get_db),
        title: Optional[str] = Query(None, description="Filter by book title"),
        author_id: Optional[int] = Query(None, description="Filter by author ID"),
        genre: Optional[str] = Query(None, description="Filter by genre"),
        min_year: Optional[int] = Query(None, description="Filter by minimum published year"),
        max_year: Optional[int] = Query(None, description="Filter by maximum published year"),
        sort_by: Optional[str] = Query("title", description="Sort field"),
        sort_order: Optional[str] = Query("asc", description="Sort order ('asc' or 'desc')"),
        page: int = Query(1, description="Page number"),
        page_size: int = Query(10, description="Number of items per page")
):
    filters = {"title": title, "author_id": author_id, "genre": genre, "published_year__gte": min_year,
               "published_year__lte": max_year}
    return await get_books(db, filters, sort_by, sort_order, page, page_size)


@router.post("/bulk-import")
async def import_books(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(Permissions.is_authenticated)
):
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return await bulk_import_books(db, file_path)
