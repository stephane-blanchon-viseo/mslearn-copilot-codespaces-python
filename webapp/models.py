import math
import re
from datetime import datetime
from typing import Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field, field_validator

T = TypeVar('T')

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _check_email(value):
    if value is not None and not EMAIL_RE.match(value):
        raise ValueError('invalid email address')
    return value


class Body(BaseModel):
    length: Union[int, None] = 20


class UserCreate(BaseModel):
    name: str
    email: str

    _validate_email = field_validator('email')(_check_email)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

    _validate_email = field_validator('email')(_check_email)


class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description='1-based page number', examples=[1])
    page_size: int = Field(20, ge=1, le=100, description='Items per page (max 100)', examples=[20])


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int = Field(description='Total number of items across all pages')
    page: int
    page_size: int
    total_pages: int = Field(description='Number of pages; 0 when there are no items')

    @classmethod
    def create(cls, items: List[T], total: int, params: PaginationParams) -> 'PaginatedResponse[T]':
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=math.ceil(total / params.page_size),
        )
