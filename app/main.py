from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db
from app.routes import books, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Book Management System", version="1.0.0", lifespan=lifespan)
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(auth.router, prefix="", tags=["users"])
