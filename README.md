
# FastAPI Books

A FastAPI-based application for managing books, authors, and users.

## Setup Instructions



### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/boychukmk/Library.git
   cd Library
   ```
2. Create .venv:
   ```sh
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ``` 

3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add your db (example):
   ```
   echo -e "DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/db_name" > .env
   ```

5. Apply database migrations:
   ```sh
   alembic upgrade head
   ```

5. Start the FastAPI server:
   ```sh
    uvicorn app.main:app --reload
   ```

## API Endpoints

### Books

| Method  | Endpoint                | Description      |
|---------|-------------------------|------------------|
| **POST**   | `/books`            | Add a book       |
| **GET**    | `/books`            | List all books   |
| **GET**    | `/books/{book_id}`  | Get book details |
| **PUT**    | `/books/{book_id}`  | Update book info |
| **DELETE** | `/books/{book_id}`  | Delete a book    |
| **POST**   | `/books/import`     | Bulk import books |

### Users

| Method  | Endpoint    | Description     |
|---------|------------|-----------------|
| **POST**   | `/register` | Register a user  |
| **POST**   | `/login`    | User login       |

## Documentation
Once the server is running, API documentation is available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Running Tests
To run the tests, use:
```sh
coverage run -m pytest --asyncio-mode=auto && coverage report
```

To test bulk import functionality you can yose 10_books.json stored in project root
