"""System settings: key-value configuration store, plus system health snapshot."""

from sqlalchemy import select, func

from database.connection import get_session
from models.settings import SystemSetting
from models.people import StudentProfile, TeacherProfile, ParentProfile
from models.school import SchoolClass

DEFAULT_SETTINGS = {
    "maintenance_mode": "off",
    "min_password_length": "8",
    "allow_teacher_self_registration": "on",
    "allow_parent_self_registration": "on",
}


def ensure_default_settings():
    db = get_session()
    try:
        for key, value in DEFAULT_SETTINGS.items():
            existing = db.execute(select(SystemSetting).where(SystemSetting.key == key)).scalar_one_or_none()
            if existing is None:
                db.add(SystemSetting(key=key, value=value))
        db.commit()
    finally:
        db.close()


def get_setting(key: str, default: str = "") -> str:
    db = get_session()
    try:
        setting = db.execute(select(SystemSetting).where(SystemSetting.key == key)).scalar_one_or_none()
        return setting.value if setting else default
    finally:
        db.close()


def set_setting(key: str, value: str) -> tuple[bool, str]:
    db = get_session()
    try:
        setting = db.execute(select(SystemSetting).where(SystemSetting.key == key)).scalar_one_or_none()
        if setting is None:
            db.add(SystemSetting(key=key, value=value))
        else:
            setting.value = value
        db.commit()
        return True, "Setting saved."
    finally:
        db.close()


def list_all_settings() -> list[SystemSetting]:
    db = get_session()
    try:
        return list(db.execute(select(SystemSetting)).scalars().all())
    finally:
        db.close()


def system_health_snapshot() -> dict:
    db = get_session()
    try:
        return {
            "students": db.execute(select(func.count(StudentProfile.id))).scalar_one(),
            "teachers": db.execute(select(func.count(TeacherProfile.id))).scalar_one(),
            "parents": db.execute(select(func.count(ParentProfile.id))).scalar_one(),
            "classes": db.execute(select(func.count(SchoolClass.id))).scalar_one(),
        }
    finally:
        db.close()
