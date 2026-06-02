from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.db.main import init_db

#ROUTES
from src.books.routes import book_router
from src.auth.routes import auth_router
from src.reviews.routes import review_router
from src.tags.routers import tags_router

#Errors
from .errors import register_all_errors
from.middleware import register_middleware

#life span event
@asynccontextmanager
async def life_span(app: FastAPI):
    print(f"server is starting------")
    #update db when server starts
    await init_db()
    yield
    print(f"server has stopped------")

version = "V1"
app = FastAPI(
    title="Bookly",
    description="A REST API for a book review web service",
    version= version
)

# Registering exception handlers
register_all_errors(app)

# middleware
register_middleware(app)

app.include_router(book_router, prefix=f"/api/{version}/books", tags=['books'])
app.include_router(auth_router, prefix=f'/api/{version}/auth', tags=['auth'])
app.include_router(review_router, prefix=f'/api/{version}/reviews', tags=['reviews'])
app.include_router(tags_router, prefix=f"/api/{version}/tags", tags=["tags"])