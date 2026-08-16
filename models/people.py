"""Role-specific profiles: students, parents, teachers, and parent-child links."""

from sqlalchemy import Column, String, Boolean, Date, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel


class TeacherProfile(BaseModel):
    __tablename__ = "teacher_profiles"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    employee_id = Column(String(50), nullable=True, unique=True)
    qualification = Column(String(255), nullable=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    employment_date = Column(Date, nullable=True)
    employment_status = Column(String(50), default="active", nullable=False)   # active, on_leave, terminated
    approval_status = Column(String(20), default="pending", nullable=False)    # pending, approved, rejected
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    bio = Column(Text, nullable=True)

    # The class requested at registration time. This is the single source of
    # truth for "which class did this teacher ask for" until an admin approves
    # them, at which point SchoolClass.class_teacher_id becomes authoritative.
    requested_class_id = Column(String(36), ForeignKey("school_classes.id"), nullable=True)

    user = relationship("User", back_populates="teacher_profile", foreign_keys=[user_id])
    department = relationship("Department")
    classes_as_teacher = relationship(
        "SchoolClass", back_populates="class_teacher", foreign_keys="SchoolClass.class_teacher_id"
    )


class ParentProfile(BaseModel):
    __tablename__ = "parent_profiles"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    occupation = Column(String(150), nullable=True)
    relationship_type = Column(String(50), nullable=True)   # father, mother, guardian
    alternate_phone = Column(String(20), nullable=True)

    user = relationship("User", back_populates="parent_profile", foreign_keys=[user_id])
    children_links = relationship("ParentStudentLink", back_populates="parent")


class StudentProfile(BaseModel):
    __tablename__ = "student_profiles"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)   # nullable: some students have no login
    admission_number = Column(String(50), nullable=False, unique=True)
    current_class_id = Column(String(36), ForeignKey("school_classes.id"), nullable=True)
    student_status = Column(String(20), default="active", nullable=False)   # active, inactive, graduated
    emergency_contact_name = Column(String(150), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    user = relationship("User", back_populates="student_profile", foreign_keys=[user_id])
    current_class = relationship("SchoolClass", back_populates="students")
    parent_links = relationship("ParentStudentLink", back_populates="student")


class ParentStudentLink(BaseModel):
    """Explicit many-to-many link so a child can have multiple guardians and vice versa."""

    __tablename__ = "parent_student_links"

    parent_id = Column(String(36), ForeignKey("parent_profiles.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False)
    is_primary_guardian = Column(Boolean, default=False, nullable=False)

    parent = relationship("ParentProfile", back_populates="children_links")
    student = relationship("StudentProfile", back_populates="parent_links")
