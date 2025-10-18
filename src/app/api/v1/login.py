from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import DuplicateValueException, UnauthorizedException
from ...core.schemas import Token
from ...core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    TokenType,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_token,
)
from ...crud.crud_users import crud_users
from ...schemas.user import UserCreate, UserCreateInternal, UserRead

router = APIRouter(tags=["login"])


@router.post("/signup", response_model=UserRead, status_code=201)
async def signup(
    request: Request, user: UserCreate, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> UserRead:
    """
    Create a new user account.

    - **name**: Full name of the user
    - **username**: Unique username for the account
    - **email**: Valid email address
    - **password**: Strong password for the account
    """
    # Check if email already exists
    email_exists = await crud_users.exists(db=db, email=user.email)
    if email_exists:
        raise DuplicateValueException("Email is already registered")

    # Check if username already exists
    username_exists = await crud_users.exists(db=db, username=user.username)
    if username_exists:
        raise DuplicateValueException("Username not available")

    # Hash the password and create user
    user_internal_dict = user.model_dump()
    user_internal_dict["hashed_password"] = get_password_hash(password=user_internal_dict["password"])
    del user_internal_dict["password"]

    user_internal = UserCreateInternal(**user_internal_dict)
    created_user = await crud_users.create(db=db, object=user_internal)

    # Retrieve and return the created user
    user_read = await crud_users.get(db=db, id=created_user.id, schema_to_select=UserRead)
    return user_read


@router.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    user = await authenticate_user(username_or_email=form_data.username, password=form_data.password, db=db)
    if not user:
        raise UnauthorizedException("Wrong username, email or password.")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)

    refresh_token = await create_refresh_token(data={"sub": user["username"]})
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="lax", max_age=max_age
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh")
async def refresh_access_token(request: Request, db: AsyncSession = Depends(async_get_db)) -> dict[str, str]:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise UnauthorizedException("Refresh token missing.")

    user_data = await verify_token(refresh_token, TokenType.REFRESH, db)
    if not user_data:
        raise UnauthorizedException("Invalid refresh token.")

    new_access_token = await create_access_token(data={"sub": user_data.username_or_email})
    return {"access_token": new_access_token, "token_type": "bearer"}
