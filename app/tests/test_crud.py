import pytest
import json
from sqlalchemy import text
from app.schemas.book import BookCreate, BookUpdate
from app.crud.raw_sql_crud import (
    validate_or_create_author,
    create_book,
    get_book_by_id,
    update_book,
    delete_book,
    get_books,
    bulk_import_books,
)


@pytest.mark.asyncio
async def test_validate_or_create_author_existing(test_db_session):
    author_name = "J.K. Rowling"
    await test_db_session.execute(
        text("INSERT INTO authors (name) VALUES (:author_name)"),
        {"author_name": author_name}
    )
    await test_db_session.commit()

    author_id = await validate_or_create_author(test_db_session, author_name)
    assert author_id is not None


@pytest.mark.asyncio
async def test_validate_or_create_author_create(test_db_session):
    author_name = "New Author"
    author_id = await validate_or_create_author(test_db_session, author_name)

    result = await test_db_session.execute(
        text("SELECT id FROM authors WHERE name = :author_name"),
        {"author_name": author_name}
    )
    author = result.fetchone()
    assert author is not None
    assert author[0] == author_id


@pytest.mark.asyncio
async def test_create_book(test_db_session):
    book_data = BookCreate(title="Harry Potter", genre="Fantasy", published_year=1997, author="J.K. Rowling")

    created_book = await create_book(test_db_session, book_data)

    assert created_book["title"] == book_data.title
    assert created_book["author"]["name"] == book_data.author
    assert created_book["genre"] == book_data.genre
    assert created_book["published_year"] == book_data.published_year


@pytest.mark.asyncio
async def test_get_book_by_id(test_db_session):
    book_data = BookCreate(title="Harry Potter", genre="Fantasy", published_year=1997, author="J.K. Rowling")
    created_book = await create_book(test_db_session, book_data)

    book = await get_book_by_id(test_db_session, created_book["id"])

    assert book["title"] == created_book["title"]
    assert book["author"]["name"] == created_book["author"]["name"]


@pytest.mark.asyncio
async def test_delete_book(test_db_session):
    book_data = BookCreate(title="Harry Potter", genre="Fantasy", published_year=1997, author="J.K. Rowling")
    created_book = await create_book(test_db_session, book_data)

    response = await delete_book(test_db_session, created_book["id"])

    assert response["message"] == f"Book with ID {created_book['id']} has been deleted"

    result = await test_db_session.execute(
        text("SELECT id FROM books WHERE id = :book_id"),
        {"book_id": created_book["id"]}
    )
    assert result.fetchone() is None


@pytest.mark.asyncio
async def test_get_books(test_db_session):
    book_data = BookCreate(title="Harry Potter", genre="Fantasy", published_year=1997, author="J.K. Rowling")
    created_book = await create_book(test_db_session, book_data)

    filters = {"title": "Harry Potter"}
    books = await get_books(test_db_session, filters)

    assert len(books) > 0
    assert books[0]["title"] == created_book["title"]


@pytest.mark.asyncio
async def test_bulk_import_books_json(test_db_session, tmp_path):
    file_path = tmp_path / "books.json"
    books_data = [
        {"title": "Book 1", "genre": "Fantasy", "published_year": 2020, "author": "Author 1"},
        {"title": "Book 2", "genre": "Sci-Fi", "published_year": 2021, "author": "Author 2"}
    ]

    with open(file_path, "w") as f:
        json.dump(books_data, f)

    response = await bulk_import_books(test_db_session, str(file_path))

    assert response["message"] == "Successfully imported 2 books"
