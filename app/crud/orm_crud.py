from sqlalchemy import desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from sqlalchemy.orm import joinedload

from app.models.author import Author
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate
from app.core.config import settings
import json
import csv


async def validate_or_create_author(db: AsyncSession, author_name: str):
    if not author_name or not author_name.strip():
        raise HTTPException(status_code=400, detail="Author name cannot be empty")

    result = await db.execute(select(Author).where(Author.name == author_name))
    author = result.scalars().first()

    if not author:
        author = Author(name=author_name)
        db.add(author)
        await db.commit()
        await db.refresh(author)

    return author


async def create_book(db: AsyncSession, book: BookCreate):
    if not book.title or not book.title.strip():
        raise HTTPException(status_code=400, detail="Book title cannot be empty")

    author = await validate_or_create_author(db, book.author)

    new_book = Book(
        title=book.title,
        genre=book.genre,
        published_year=book.published_year,
        author_id=author.id
    )
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)

    return {"id": new_book.id, "title": new_book.title, "genre": new_book.genre,
            "published_year": new_book.published_year, "author": {"id": author.id, "name": author.name}}


async def get_book_by_id(db: AsyncSession, book_id: int):
    query = select(Book).options(joinedload(Book.author)).where(Book.id == book_id)

    result = await db.execute(query)
    book = result.scalars().first()

    if not book:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

    return {
        "id": book.id,
        "title": book.title,
        "genre": book.genre,
        "published_year": book.published_year,
        "author": {"id": book.author.id, "name": book.author.name},
    }


async def update_book(db: AsyncSession, book_id: int, book: BookUpdate):
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid book ID")

    result = await db.execute(select(Book).where(Book.id == book_id))
    book_db = result.scalars().first()

    if not book_db:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

    update_data = book.model_dump(exclude_unset=True)

    if "author" in update_data:
        author = await validate_or_create_author(db, update_data.pop("author"))
        book_db.author_id = author.id

    for key, value in update_data.items():
        setattr(book_db, key, value)

    await db.commit()
    await db.refresh(book_db)

    return {"id": book_db.id, "title": book_db.title, "genre": book_db.genre,
            "published_year": book_db.published_year, "author": {"id": book_db.author.id, "name": book_db.author.name}}


async def delete_book(db: AsyncSession, book_id: int):
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid book ID")

    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalars().first()

    if not book:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

    await db.delete(book)
    await db.commit()

    return {"message": f"Book with ID {book_id} has been deleted"}


async def get_books(
    db: AsyncSession,
    filters: dict,
    sort_by: str = "title",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = settings.PAGE_SIZE
):

    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="Page number and page size must be positive integers")

    valid_sort_fields = {"title", "genre", "published_year"}
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

    query = select(Book).options(joinedload(Book.author))

    for attr, value in filters.items():
        if value is not None:
            field_name = attr.split("__")[0]
            query = query.where(getattr(Book, field_name) == value)

    order_by_clause = getattr(Book, sort_by)
    if sort_order.lower() == "desc":
        order_by_clause = desc(order_by_clause)
    else:
        order_by_clause = asc(order_by_clause)

    query = query.order_by(order_by_clause).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    books = result.scalars().all()

    return [
        {
            "id": book.id,
            "title": book.title,
            "genre": book.genre,
            "published_year": book.published_year,
            "author": {"id": book.author.id, "name": book.author.name},
        }
        for book in books
    ]


async def bulk_import_books(db: AsyncSession, file_path: str):
    books = []
    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            books = json.load(f)
    elif file_path.endswith(".csv"):
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            books = [row for row in reader]
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    book_instances = []
    for book in books:
        author = await validate_or_create_author(db, book.get("author"))
        book_instances.append(Book(
            title=book.get("title"),
            genre=book.get("genre"),
            published_year=book.get("published_year"),
            author_id=author.id
        ))

    db.add_all(book_instances)
    await db.commit()

    return {"message": f"Successfully imported {len(book_instances)} books"}
