from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import HTTPException
from app.schemas.book import BookCreate, BookUpdate
from app.core.config import settings
import json
import csv


async def validate_or_create_author(db: AsyncSession, author_name: str):
    if not author_name or not author_name.strip():
        raise HTTPException(status_code=400, detail="Author name cannot be empty")

    query_author = text("SELECT id FROM authors WHERE name = :author_name")
    result = await db.execute(query_author, {"author_name": author_name})
    author = result.fetchone()

    if not author:
        query_insert_author = text("INSERT INTO authors (name) VALUES (:author_name) RETURNING id")
        result = await db.execute(query_insert_author, {"author_name": author_name})
        author = result.fetchone()
        if not author:
            raise HTTPException(status_code=500, detail="Failed to create author")
        await db.commit()

    return author[0]


async def create_book(db: AsyncSession, book: BookCreate):
    if not book.title or not book.title.strip():
        raise HTTPException(status_code=400, detail="Book title cannot be empty")

    author_id = await validate_or_create_author(db, book.author)

    query_insert_book = text("""
        INSERT INTO books (title, genre, published_year, author_id)
        VALUES (:title, :genre, :published_year, :author_id)
        RETURNING id, title, genre, published_year, author_id
    """)
    result = await db.execute(query_insert_book, {
        "title": book.title,
        "genre": book.genre,
        "published_year": book.published_year,
        "author_id": author_id
    })
    book_data = result.fetchone()

    if not book_data:
        raise HTTPException(status_code=500, detail="Failed to create book")

    await db.commit()

    book_dict = dict(zip(result.keys(), book_data))
    book_dict["author"] = {"id": author_id, "name": book.author}

    return book_dict


async def get_book_by_id(db: AsyncSession, book_id: int):
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid book ID")

    query = text("""
    SELECT books.*, authors.id AS author_id, authors.name AS author_name 
    FROM books 
    JOIN authors ON books.author_id = authors.id
    WHERE books.id = :book_id
    """)
    result = await db.execute(query, {"book_id": book_id})
    book = result.fetchone()

    if not book:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

    book_dict = dict(zip(result.keys(), book))
    book_dict["author"] = {"id": book_dict["author_id"], "name": book_dict.pop("author_name")}
    book_dict.pop("author_id")

    return book_dict


async def update_book(db: AsyncSession, book_id: int, book: BookUpdate):
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid book ID")

    book_data = book.model_dump(exclude_unset=True)

    if "author" in book_data:
        author_id = await validate_or_create_author(db, book_data["author"])
        book_data["author_id"] = author_id
        book_data.pop("author", None)

    if not book_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    set_clause = ", ".join(f"{key} = :{key}" for key in book_data.keys())

    query = text(f"""
    UPDATE books 
    SET {set_clause} 
    WHERE id = :book_id 
    RETURNING books.*, (SELECT name FROM authors WHERE authors.id = books.author_id) AS author_name
    """)
    book_data["book_id"] = book_id

    result = await db.execute(query, book_data)
    updated_book = result.fetchone()

    if not updated_book:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

    await db.commit()

    updated_book_dict = dict(zip(result.keys(), updated_book))
    updated_book_dict["author"] = {"id": updated_book_dict["author_id"], "name": updated_book_dict.pop("author_name")}
    updated_book_dict.pop("author_id")

    return updated_book_dict


async def delete_book(db: AsyncSession, book_id: int):
    if book_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid book ID")

    query = text("DELETE FROM books WHERE id = :book_id RETURNING id")
    result = await db.execute(query, {"book_id": book_id})

    if not result.fetchone():
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")

    await db.commit()
    return {"message": f"Book with ID {book_id} has been deleted"}


async def get_books(db: AsyncSession, filters: dict, sort_by: str = "title", sort_order: str = "asc",
                    page: int = 1, page_size: int = settings.PAGE_SIZE):
    if page < 1 or page_size < 1:
        raise HTTPException(status_code=400, detail="Page number and page size must be positive integers")

    valid_sort_fields = {"title", "genre", "published_year"}
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_by}")

    query = text("""
    SELECT books.*, authors.id AS author_id, authors.name AS author_name
    FROM books 
    JOIN authors ON books.author_id = authors.id
    """)

    filter_clauses = []
    query_params = {}

    for attr, value in filters.items():
        if value is not None:
            field_name = attr.split("__")[0]
            filter_clauses.append(f"{field_name} = :{field_name}")
            query_params[field_name] = value

    if filter_clauses:
        query = text(query.text + " WHERE " + " AND ".join(filter_clauses))

    query = text(query.text + f" ORDER BY {sort_by} {sort_order.upper()} LIMIT :limit OFFSET :offset")
    query_params["limit"] = page_size
    query_params["offset"] = (page - 1) * page_size

    result = await db.execute(query, query_params)
    books = [dict(zip(result.keys(), row)) for row in result.fetchall()]

    for book in books:
        book["author"] = {"id": book.pop("author_id"), "name": book.pop("author_name")}

    return books


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

    for book in books:
        author_id = await validate_or_create_author(db, book.get("author"))
        book["author_id"] = author_id

    query = text("""
    INSERT INTO books (title, genre, published_year, author_id) 
    VALUES (:title, :genre, :published_year, :author_id)
    """)
    await db.execute(query, books)
    await db.commit()

    return {"message": f"Successfully imported {len(books)} books"}
