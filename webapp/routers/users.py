from fastapi import APIRouter, Depends, HTTPException, Query, Response

from webapp.dependencies import get_user_service
from webapp.models import PaginatedResponse, PaginationParams, User, UserCreate, UserUpdate
from webapp.services.user_service import UserService

router = APIRouter(prefix='/users', tags=['users'])


@router.post('', response_model=User, status_code=201)
def create_user(data: UserCreate, service: UserService = Depends(get_user_service)):
    return service.create(data)


def get_pagination(
    page: int = Query(1, ge=1, description='1-based page number', examples=[1]),
    page_size: int = Query(20, ge=1, le=100, description='Items per page (max 100)', examples=[20]),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


@router.get(
    '',
    response_model=PaginatedResponse[User],
    summary='List users (paginated)',
    description='Returns one page of users plus pagination metadata.',
)
def list_users(
    params: PaginationParams = Depends(get_pagination),
    service: UserService = Depends(get_user_service),
):
    items, total = service.list_page(params.page, params.page_size)
    return PaginatedResponse[User].create(items, total, params)


@router.get('/{user_id}', response_model=User)
def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    user = service.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    return user


@router.put('/{user_id}', response_model=User)
def update_user(user_id: int, data: UserUpdate, service: UserService = Depends(get_user_service)):
    user = service.update(user_id, data)
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    return user


@router.delete('/{user_id}', status_code=204)
def delete_user(user_id: int, service: UserService = Depends(get_user_service)):
    if not service.delete(user_id):
        raise HTTPException(status_code=404, detail='User not found')
    return Response(status_code=204)
