from fastapi import FastAPI, status
from contextlib import asynccontextmanager
from src.db.main import init_db

#ROUTES
from src.books.routes import book_router
from src.auth.routes import auth_router
from src.reviews.routes import review_router
from src.tags.routers import tags_router

#Errors
from .errors import (
    BooklyException,
    AccessTokenRequired,
    AccountNotVerified,
    BookNotFound,
    InsufficientPermission,
    InvalidCredentials,
    InvalidToken,
    RefreshTokenRequired,
    RevokedToken,
    TagAlreadyExists,
    TagNotFound,
    UserAlreadyExists,
    UserNotFound,
    create_exception_handler
)

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
app.add_exception_handler(
    UserAlreadyExists,
    create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        message={
            "message": "User with email already exits",
            "error_code": "User_exists"
        }
    )
)

app.add_exception_handler(
    InvalidToken,
    create_exception_handler(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message={
            "message": "Invalid token provided",
            "error_code": "Invalid_token"
        }
    )
)

app.add_exception_handler(
    RevokedToken,
    create_exception_handler(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message={
            "message": "Token has been revoked",
            "error_code": "Revoked_token"
        }
    )
)

app.add_exception_handler(
    AccessTokenRequired,
    create_exception_handler(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message={
            "message": "Access token required",
            "error_code": "Access_token_required"
        }
    )
)

app.add_exception_handler(
    RefreshTokenRequired,
    create_exception_handler(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message={
            "message": "Refresh token required",
            "error_code": "Refresh_token_required"
        }
    )
)

app.add_exception_handler(
    InvalidCredentials,
    create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        message={
            "message": "Invalid email or password",
            "error_code": "Invalid_credentials"
        }
    )
)

app.add_exception_handler(
    InsufficientPermission,
    create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        message={
            "message": "Insufficient permissions",
            "error_code": "Insufficient_permission"
        }
    )
)

app.add_exception_handler(
    BookNotFound,
    create_exception_handler(
        status_code=status.HTTP_404_NOT_FOUND,
        message={
            "message": "Book not found",
            "error_code": "Book_not_found"
        }
    )
)

app.add_exception_handler(
    TagNotFound,
    create_exception_handler(
        status_code=status.HTTP_404_NOT_FOUND,
        message={
            "message": "Tag not found",
            "error_code": "Tag_not_found"
        }
    )
)

app.add_exception_handler(
    TagAlreadyExists,
    create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        message={
            "message": "Tag already exists",
            "error_code": "Tag_exists"
        }
    )
)

app.add_exception_handler(
    UserNotFound,
    create_exception_handler(
        status_code=status.HTTP_404_NOT_FOUND,
        message={
            "message": "User not found",
            "error_code": "User_not_found"
        }
    )
)

app.add_exception_handler(
    AccountNotVerified,
    create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        message={
            "message": "Account not verified",
            "error_code": "Account_not_verified"
        }
    )
)


app.include_router(book_router, prefix=f"/api/{version}/books", tags=['books'])
app.include_router(auth_router, prefix=f'/api/{version}/auth', tags=['auth'])
app.include_router(review_router, prefix=f'/api/{version}/reviews', tags=['reviews'])
app.include_router(tags_router, prefix=f"/api/{version}/tags", tags=["tags"])