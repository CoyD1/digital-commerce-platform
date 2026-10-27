from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.session import get_session
from app.users.dependencies import get_current_user
from app.users.model import User
from app.users.repository import UserRepository
from app.users.schemas import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserRead,
)
from app.users.service import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserService,
)

router = APIRouter(
    prefix="/api/v1/auth", 
    tags=["auth"]
)
users_router = APIRouter(
    prefix="/api/v1/users", 
    tags=["users"],
)

@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    repository = UserRepository(session)
    service = UserService(repository)

    try:
        async with session.begin():
            user = await service.register(data)

    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from None

    except IntegrityError as error:
        diagnostics = getattr(error.orig, "diag", None)
        constraint_name = getattr(diagnostics, "constraint_name", None)

        if constraint_name == "users_email_key":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            ) from error

        raise

    return user

@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    repository = UserRepository(session)
    service = UserService(repository)

    try:
        user = await service.authenticate(
            email=str(data.email),
            password=data.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    return TokenResponse(
        access_token=create_access_token(user.id),
    )

@users_router.get("/me", response_model=UserRead)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user