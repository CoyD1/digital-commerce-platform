from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.users.repository import UserRepository
from app.users.schemas import UserCreate, UserRead
from app.users.service import EmailAlreadyExistsError, UserService


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

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