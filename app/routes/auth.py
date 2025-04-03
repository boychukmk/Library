from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_user_by_username(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str):
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalars().first()


@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user_by_username = await get_user_by_username(db, user.username)
    existing_user_by_email = await get_user_by_email(db, user.email)

    if existing_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    if existing_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user_in_db = User(username=user.username, email=user.email, hashed_password=hash_password(user.password))
    db.add(user_in_db)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error while saving user")

    return {"message": "User created successfully"}


@router.post("/login")
async def login(request: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user_in_db = await get_user_by_username(db, username=request.username)

    if not user_in_db or not verify_password(request.password, user_in_db.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user_in_db.username})
    return {"access_token": access_token, "token_type": "bearer"}
