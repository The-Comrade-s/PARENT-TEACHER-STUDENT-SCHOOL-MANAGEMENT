"""User identity, roles, and permissions (RBAC core)."""

from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship

from models.base import BaseModel

user_roles = Table(
    "user_roles",
    BaseModel.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    BaseModel.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class User(BaseModel):
    __tablename__ = "users"

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    gender = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    address = Column(String(500), nullable=True)
    profile_photo_url = Column(String(500), nullable=True)

    # active | pending | suspended | inactive
    status = Column(String(20), nullable=False, default="active")

    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)

    roles = relationship("Role", secondary=user_roles, back_populates="users")

    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False)
    parent_profile = relationship("ParentProfile", back_populates="user", uselist=False)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def has_role(self, role_name: str) -> bool:
        return any(r.name == role_name for r in self.roles)

    def has_permission(self, permission_code: str) -> bool:
        for role in self.roles:
            for perm in role.permissions:
                if perm.code == permission_code:
                    return True
        return False


class Role(BaseModel):
    __tablename__ = "roles"

    name = Column(String(100), unique=True, nullable=False)          # e.g. super_admin
    display_name = Column(String(150), nullable=False)                # e.g. Super Administrator
    description = Column(String(500), nullable=True)
    is_system_role = Column(Boolean, default=False, nullable=False)   # protects seeded roles

    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(BaseModel):
    __tablename__ = "permissions"

    code = Column(String(150), unique=True, nullable=False)   # e.g. attendance.create
    module = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(String(300), nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(150), nullable=False)     # e.g. login, teacher.approve
    module = Column(String(100), nullable=False)      # e.g. auth, attendance
    details = Column(String(1000), nullable=True)
    ip_address = Column(String(64), nullable=True)

    user = relationship("User")
