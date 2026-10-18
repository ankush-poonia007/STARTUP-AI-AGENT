"""Authentication HTTP routes."""

from http import HTTPStatus

from fastapi import APIRouter, Depends, status

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.services import get_auth_service
from src.api.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    UserResponse,
)
from src.schemas.common import ErrorResponse
from src.repositories.models.user import User
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

_AUTH_ERRORS = {
    status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        HTTPStatus.UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await auth_service.register(payload.email, payload.password)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenPairResponse,
    responses={
        **_AUTH_ERRORS,
        HTTPStatus.UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenPairResponse:
    access_token, refresh_token = await auth_service.login(
        payload.email,
        payload.password,
    )
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    responses={
        **_AUTH_ERRORS,
        HTTPStatus.UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
async def refresh(
    payload: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AccessTokenResponse:
    access_token = await auth_service.refresh(payload.refresh_token)
    return AccessTokenResponse(access_token=access_token)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    responses={
        **_AUTH_ERRORS,
        HTTPStatus.UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    },
)
async def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    await auth_service.logout(current_user, payload.refresh_token)
    return LogoutResponse()


@router.get(
    "/me",
    response_model=UserResponse,
    responses=_AUTH_ERRORS,
)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)
