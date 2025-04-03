from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_access_token
from app.core.database import get_db
from app.crud.raw_sql_crud import get_book_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class Permissions:
    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        payload = decode_access_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return username

    @staticmethod
    async def is_authenticated(current_user: str = Depends(get_current_user)):
        return current_user
