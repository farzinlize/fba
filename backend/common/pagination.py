from __future__ import annotations

from collections.abc import Sequence
from math import ceil
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from fastapi import Depends, Query
from fastapi_pagination import pagination_ctx
from fastapi_pagination.bases import AbstractPage, AbstractParams, RawParams
from fastapi_pagination.cursor import CursorParams
from fastapi_pagination.ext.sqlalchemy import apaginate
from fastapi_pagination.links.bases import create_links
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession
    from typing_extensions import Self

T = TypeVar('T')
SchemaT = TypeVar('SchemaT')


class _CustomPageParams(BaseModel, AbstractParams):
    """Custom pagination parameters"""

    page: int = Query(1, ge=1, description='Page number')
    size: int = Query(20, gt=0, le=200, description='Items per page')

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=self.size * (self.page - 1),
        )


class _CustomCursorParams(CursorParams):
    """Custom cursor pagination parameters"""

    size: int = Query(50, ge=0, le=200, description='Items per page')


class _Links(BaseModel):
    """Pagination links"""

    first: str = Field(description='First page link')
    last: str = Field(description='Last page link')
    self: str = Field(description='Current page link')
    next: str | None = Field(None, description='Next page link')
    prev: str | None = Field(None, description='Previous page link')


class _PageDetails(BaseModel):
    """Pagination details"""

    items: list = Field([], description='Items on the current page')
    total: int = Field(description='Total item count')
    page: int = Field(description='Current page number')
    size: int = Field(description='Items per page')
    total_pages: int = Field(description='Total pages')
    links: _Links = Field(description='Pagination links')


class _CursorPageDetails(BaseModel):
    """Cursor pagination details"""

    items: list = Field([], description='Items on the current page')
    next_cursor: str | None = Field(None, description='Next page cursor')
    has_more: bool = Field(description='Whether more data is available')


class _CustomPage(_PageDetails, AbstractPage[T], Generic[T]):
    """Custom pagination class"""

    __params_type__ = _CustomPageParams

    @classmethod
    def create(
        cls,
        items: list,
        params: _CustomPageParams,
        total: int = 0,
    ) -> Self:
        page = params.page
        size = params.size
        total_pages = ceil(total / size)
        links = create_links(
            first={'page': 1, 'size': size},
            last={'page': total_pages, 'size': size} if total > 0 else {'page': 1, 'size': size},
            next={'page': page + 1, 'size': size} if (page + 1) <= total_pages else None,
            prev={'page': page - 1, 'size': size} if (page - 1) >= 1 else None,
        ).model_dump()

        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            links=links,
        )


class _CustomCursorPage(_CursorPageDetails, AbstractPage[T], Generic[T]):
    """Custom cursor pagination class"""

    __params_type__ = _CustomCursorParams

    @classmethod
    def create(
        cls,
        items: list,
        params: CursorParams,
        *,
        next_: Any = None,
        **kwargs: Any,
    ) -> Self:
        if not isinstance(params, CursorParams):
            raise TypeError('CustomCursorPage should be used with CursorParams')

        return cls(
            items=items,
            next_cursor=params.encode_cursor(next_),
            has_more=next_ is not None,
        )


class PageData(_PageDetails, Generic[SchemaT]):
    """
    Unified response model with a data schema, for paginated endpoints only

    E.g. ::

        @router.get('/test', response_model=ResponseSchemaModel[PageData[GetApiDetail]])
        def test():
            return ResponseSchemaModel[PageData[GetApiDetail]](data=GetApiDetail(...))


        @router.get('/test')
        def test() -> ResponseSchemaModel[PageData[GetApiDetail]]:
            return ResponseSchemaModel[PageData[GetApiDetail]](data=GetApiDetail(...))


        @router.get('/test')
        def test() -> ResponseSchemaModel[PageData[GetApiDetail]]:
            res = CustomResponseCode.HTTP_200
            return ResponseSchemaModel[PageData[GetApiDetail]](code=res.code, msg=res.msg, data=GetApiDetail(...))
    """

    items: Sequence[SchemaT]


class CursorPageData(_CursorPageDetails, Generic[SchemaT]):
    """Unified response model with a data schema, for cursor pagination only; used like PageData"""

    items: Sequence[SchemaT]


async def paging_data(db: AsyncSession, select: Select, **kwargs) -> dict[str, Any]:
    """
    Create paginated data using SQLAlchemy

    :param db: Database session
    :param select: SQL query
    :param kwargs: Additional fastapi-pagination apaginate parameters
    :return:
    """
    paginated_data: _CustomPage = await apaginate(db, select, **kwargs)
    page_data = paginated_data.model_dump()
    return page_data


async def cursor_paging_data(db: AsyncSession, select: Select, **kwargs) -> dict[str, Any]:
    """
    Create cursor-paginated data using SQLAlchemy

    :param db: Database session
    :param select: SQL query
    :param kwargs: Additional fastapi-pagination apaginate parameters
    :return:
    """
    paginated_data: _CustomCursorPage = await apaginate(db, select, **kwargs)
    page_data = paginated_data.model_dump()
    return page_data


# Pagination dependency injection
DependsPagination = Depends(pagination_ctx(_CustomPage))
DependsCursorPagination = Depends(pagination_ctx(_CustomCursorPage))
