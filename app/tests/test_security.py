import pytest
from datetime import timedelta
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.config import settings
from jose import jwt
from fastapi import HTTPException, status


@pytest.mark.parametrize("password", ["password123", "securePass!", "12345678"])
def test_hash_and_verify_password(password):
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data, timedelta(minutes=5))

    assert isinstance(token, str)

    decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded_data["sub"] == "testuser"
    assert "exp" in decoded_data


def test_decode_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data, timedelta(minutes=5))

    decoded = decode_access_token(token)
    assert decoded["sub"] == "testuser"

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("invalid_token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid or expired token"

