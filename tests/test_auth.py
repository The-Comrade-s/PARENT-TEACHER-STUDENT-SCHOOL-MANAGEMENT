from auth.security import hash_password, verify_password, password_meets_policy
from services import auth_service


def test_password_hash_roundtrip():
    hashed = hash_password("Sup3rSecret!")
    assert verify_password("Sup3rSecret!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_password_policy_rejects_weak_passwords():
    ok, _ = password_meets_policy("short")
    assert not ok
    ok, _ = password_meets_policy("nouppercase123")
    assert not ok
    ok, _ = password_meets_policy("GoodPass123")
    assert ok


def test_seed_creates_default_admin():
    auth_service.seed_roles_and_admin()
    user, message = auth_service.authenticate("admin@ptms.local", "ChangeMe123!")
    assert user is not None
    assert user.has_role("super_admin")


def test_register_parent_success_and_duplicate_rejected():
    ok, message = auth_service.register_parent("Jane", "Doe", "jane@example.com", "GoodPass123")
    assert ok, message

    ok2, message2 = auth_service.register_parent("Jane", "Doe", "jane@example.com", "GoodPass123")
    assert not ok2
    assert "already exists" in message2


def test_register_teacher_is_pending_by_default():
    auth_service.seed_roles_and_admin()
    ok, message = auth_service.register_teacher("Tom", "Smith", "tom@example.com", "GoodPass123", None)
    assert ok, message

    user, auth_message = auth_service.authenticate("tom@example.com", "GoodPass123")
    assert user is None
    assert "pending" in auth_message.lower()


def test_login_lockout_after_repeated_failures():
    auth_service.seed_roles_and_admin()
    auth_service.register_parent("Jane", "Doe", "jane2@example.com", "GoodPass123")

    from config.settings import settings

    for _ in range(settings.max_failed_login_attempts):
        auth_service.authenticate("jane2@example.com", "WrongPassword1")

    user, message = auth_service.authenticate("jane2@example.com", "GoodPass123")
    assert user is None
    assert "locked" in message.lower()
