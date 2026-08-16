"""Security and campus-safety tracking module."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel


class StudentCheckRecord(BaseModel):
    """A single check-in or check-out event for a student."""

    __tablename__ = "student_check_records"

    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False)
    check_type = Column(String(10), nullable=False)   # in, out
    recorded_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String(300), nullable=True)

    student = relationship("StudentProfile")


class PickupAuthorization(BaseModel):
    __tablename__ = "pickup_authorizations"

    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False)
    authorized_by = Column(String(36), ForeignKey("users.id"), nullable=False)   # parent
    authorized_person_name = Column(String(255), nullable=False)
    pin_code = Column(String(10), nullable=False)
    is_used = Column(String(10), default="no", nullable=False)   # no, yes
    verified_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("StudentProfile")


class Visitor(BaseModel):
    __tablename__ = "visitors"

    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    purpose = Column(String(300), nullable=True)
    host_name = Column(String(255), nullable=True)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    checked_out_at = Column(DateTime(timezone=True), nullable=True)
    recorded_by = Column(String(36), ForeignKey("users.id"), nullable=True)


class Incident(BaseModel):
    __tablename__ = "incidents"

    reported_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="low", nullable=False)   # low, medium, high
    status = Column(String(20), default="open", nullable=False)    # open, investigating, resolved


class StudentMovement(BaseModel):
    """Tracks a student leaving and returning to campus/class during the day (e.g. clinic visit)."""

    __tablename__ = "student_movements"

    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False)
    destination = Column(String(255), nullable=False)
    logged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    departed_at = Column(DateTime(timezone=True), nullable=True)
    returned_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("StudentProfile")


class EmergencyAlert(BaseModel):
    __tablename__ = "emergency_alerts"

    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)   # e.g. fire, lockdown, medical
    message = Column(Text, nullable=False)
    alert_status = Column(String(10), default="active", nullable=False)   # active, cleared
