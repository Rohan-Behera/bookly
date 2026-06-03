from typing import List

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import (
    RoleChecker,
    get_tag_service,
)
from src.books.schemas import BookModel
from src.db.main import get_session

from .schemas import TagAddModel, TagCreateModel, TagModel
from .services import TagService

tags_router = APIRouter()


@tags_router.get("/", response_model=List[TagModel])
async def get_all_tags(
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(RoleChecker(["user", "admin"])),
    tag_service: TagService = Depends(get_tag_service),
):
    return await tag_service.get_tags(session)


@tags_router.post("/", response_model=TagModel, status_code=status.HTTP_201_CREATED)
async def add_tag(
    tag_data: TagCreateModel,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(RoleChecker(["user", "admin"])),
    tag_service: TagService = Depends(get_tag_service),
) -> TagModel:
    return await tag_service.add_tag(tag_data=tag_data, session=session)


@tags_router.post("/book/{book_uid}/tags", response_model=BookModel)
async def add_tags_to_book(
    book_uid: str,
    tag_data: TagAddModel,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(RoleChecker(["user", "admin"])),
    tag_service: TagService = Depends(get_tag_service),
) -> BookModel:
    return await tag_service.add_tags_to_book(
        book_uid=book_uid, tag_data=tag_data, session=session
    )


@tags_router.put("/{tag_uid}", response_model=TagModel)
async def update_tag(
    tag_uid: str,
    tag_update_data: TagCreateModel,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(RoleChecker(["user", "admin"])),
    tag_service: TagService = Depends(get_tag_service),
) -> TagModel:
    return await tag_service.update_tag(tag_uid, tag_update_data, session)


@tags_router.delete("/{tag_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_uid: str,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(RoleChecker(["user", "admin"])),
    tag_service: TagService = Depends(get_tag_service),
) -> None:
    return await tag_service.delete_tag(tag_uid, session)
