"""Attendance, assignments, grading configuration, and results."""

from sqlalchemy import Column, String, Integer, Float, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel


class AttendanceRecord(BaseModel):
    __tablename__ = "attendance_records"

    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False)
    class_id = Column(String(36), ForeignKey("school_classes.id"), nullable=False)
    term_id = Column(String(36), ForeignKey("academic_terms.id"), nullable=True)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="present")   # present, absent, late, excused
    marked_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_locked = Column(Boolean, default=False, nullable=False)
    notes = Column(String(300), nullable=True)

    student = relationship("StudentProfile")


class Assignment(BaseModel):
    __tablename__ = "assignments"

    class_id = Column(String(36), ForeignKey("school_classes.id"), nullable=False)
    subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=True)
    teacher_id = Column(String(36), ForeignKey("teacher_profiles.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)

    submissions = relationship("AssignmentSubmission", back_populates="assignment")


class AssignmentSubmission(BaseModel):
    __tablename__ = "assignment_submissions"

    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False)
    submission_text = Column(Text, nullable=True)
    submitted_at_status = Column(String(20), default="not_submitted", nullable=False)  # not_submitted, submitted, late, reviewed
    teacher_feedback = Column(Text, nullable=True)
    score = Column(Float, nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("StudentProfile")


class GradingSystem(BaseModel):
    """Configurable grade bands, e.g. A: 70-100, B: 60-69, ... Not hardcoded."""

    __tablename__ = "grading_systems"

    name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    bands = relationship("GradeBand", back_populates="grading_system")


class GradeBand(BaseModel):
    __tablename__ = "grade_bands"

    grading_system_id = Column(String(36), ForeignKey("grading_systems.id"), nullable=False)
    grade = Column(String(10), nullable=False)          # e.g. A, B, C
    min_score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    remark = Column(String(100), nullable=True)          # e.g. Excellent
    grade_point = Column(Float, nullable=True)

    grading_system = relationship("GradingSystem", back_populates="bands")


class AssessmentConfig(BaseModel):
    """Defines how CA vs exam scores are weighted, configurable per school."""

    __tablename__ = "assessment_configs"

    name = Column(String(100), nullable=False)
    ca_weight = Column(Float, nullable=False, default=40)
    exam_weight = Column(Float, nullable=False, default=60)
    is_default = Column(Boolean, default=False, nullable=False)


class Result(BaseModel):
    __tablename__ = "results"

    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False)
    class_id = Column(String(36), ForeignKey("school_classes.id"), nullable=False)
    subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
    term_id = Column(String(36), ForeignKey("academic_terms.id"), nullable=False)
    teacher_id = Column(String(36), ForeignKey("teacher_profiles.id"), nullable=True)

    ca_score = Column(Float, default=0, nullable=False)
    exam_score = Column(Float, default=0, nullable=False)
    total_score = Column(Float, default=0, nullable=False)
    grade = Column(String(10), nullable=True)
    remark = Column(String(100), nullable=True)

    status = Column(String(20), default="draft", nullable=False)   # draft, submitted, reviewed, published

    student = relationship("StudentProfile")
    subject = relationship("Subject")
