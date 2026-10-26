from app.core.security import hash_password, verify_password


def test_correct_password_matches_hash():
    password = "example-password"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)

def test_wrong_password_does_not_match_hash():
    password_hash = hash_password("example-password")

    assert not verify_password("wrong-password", password_hash)
