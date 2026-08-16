"""School setup: profile, sessions, terms, departments, classes, subjects."""

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel


class SchoolProfile(BaseModel):
    __tablename__ = "school_profile"

    name = Column(String(255), nullable=False)
    motto = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(150), nullable=True)
    state = Column(String(150), nullable=True)
    country = Column(String(150), nullable=True)
    postal_code = Column(String(20), nullable=True)
    school_type = Column(String(100), nullable=True)      # e.g. private, public
    school_level = Column(String(100), nullable=True)     # e.g. primary, secondary
    principal_name = Column(String(255), nullable=True)
    established_year = Column(Integer, nullable=True)
    logo_url = Column(String(500), nullable=True)


class AcademicSession(BaseModel):
    __tablename__ = "academic_sessions"

    name = Column(String(50), nullable=False)   # e.g. 2025/2026
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)

    terms = relationship("AcademicTerm", back_populates="session")


class AcademicTerm(BaseModel):
    __tablename__ = "academic_terms"

    session_id = Column(String(36), ForeignKey("academic_sessions.id"), nullable=False)
    name = Column(String(50), nullable=False)   # e.g. First Term
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)

    session = relationship("AcademicSession", back_populates="terms")


class Department(BaseModel):
    __tablename__ = "departments"

    name = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    subjects = relationship("Subject", back_populates="department")


class SchoolClass(BaseModel):
    __tablename__ = "school_classes"

    name = Column(String(100), nullable=False)          # e.g. JSS 1A
    level = Column(String(50), nullable=True)            # e.g. JSS1
    capacity = Column(Integer, default=40, nullable=False)
    class_teacher_id = Column(String(36), ForeignKey("teacher_profiles.id"), nullable=True)

    class_teacher = relationship(
        "TeacherProfile", back_populates="classes_as_teacher", foreign_keys=[class_teacher_id]
    )
    students = relationship("StudentProfile", back_populates="current_class")


class Subject(BaseModel):
    __tablename__ = "subjects"

    name = Column(String(150), nullable=False)
    code = Column(String(30), nullable=False, unique=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)

    department = relationship("Department", back_populates="subjects")
