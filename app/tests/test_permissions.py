import pytest
from fastapi import HTTPException, status
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.book import Book
from app.crud.raw_sql_crud import get_book_by_id
from app.core.permissions import Permissions

from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def test_user(test_db_session: AsyncSession):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpassword")
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def test_book(test_db_session: AsyncSession, test_user):
    book = Book(id=1, title="Test Book", genre="Fiction", published_year=2020, author_id=test_user.id)
    test_db_session.add(book)
    await test_db_session.commit()
    await test_db_session.refresh(book)

    retrieved_book = await get_book_by_id(test_db_session, 1)
    print(f"DEBUG: Retrieved book from DB - {retrieved_book}")

    return book


@pytest.fixture
def access_token(test_user):
    data = {"sub": test_user.username}
    return create_access_token(data, timedelta(minutes=30))


@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(access_token, test_db_session):
    username = await Permissions.get_current_user(access_token, test_db_session)
    assert username == "testuser"


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_token(test_db_session):
    with pytest.raises(HTTPException) as exc_info:
        await Permissions.get_current_user("invalid_token", test_db_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid or expired token"


@pytest.mark.asyncio
async def test_is_authenticated():
    user = await Permissions.is_authenticated(current_user="testuser")
    assert user == "testuser"
