import pytest
from pydantic import ValidationError

from app.users.schemas import UserCreate


def test_user_create_strips_name():
    user = UserCreate(
        name="  Alice  ",
        email="alice@example.com",
        password="example-password",
    )

    assert user.name == "Alice"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "   "),
        ("name", "a" * 51),
        ("email", "invalid-email"),
        ("password", "short"),
        ("password", "a" * 129),
    ],
)
def test_user_create_rejects_invalid_fields(field, value):
    data = {
        "name": "Alice",
        "email": "alice@example.com",
        "password": "example-password",
    }
    data[field] = value

    with pytest.raises(ValidationError) as error:
        UserCreate(**data)

    assert any(item["loc"] == (field,) for item in error.value.errors())
