import pytest
from fastapi import HTTPException, status

from app.users.dependencies import require_admin
from app.users.model import User, UserRole


@pytest.mark.asyncio
async def test_require_admin_rejects_customer():
    user = User(role=UserRole.CUSTOMER)

    with pytest.raises(HTTPException) as error:
        await require_admin(current_user=user)

    assert error.value.status_code == status.HTTP_403_FORBIDDEN
    assert error.value.detail == "Admin access required"


@pytest.mark.asyncio
async def test_require_admin_accepts_admin():
    user = User(role=UserRole.ADMIN)

    result = await require_admin(current_user=user)

    assert result is user
