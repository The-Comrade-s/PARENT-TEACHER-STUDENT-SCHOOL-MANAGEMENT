"""Security and campus-safety business logic."""

import random
import string
from datetime import datetime, timezone

from sqlalchemy import select, func

from database.connection import get_session
from models.security import (
    StudentCheckRecord, PickupAuthorization, Visitor, Incident, StudentMovement, EmergencyAlert,
)


def _now():
    return datetime.now(timezone.utc)


# ------------------------------------------------------------ check in/out --

def check_in_student(student_id: str, recorded_by: str, notes: str = "") -> tuple[bool, str]:
    db = get_session()
    try:
        db.add(StudentCheckRecord(
            student_id=student_id, check_type="in", recorded_by=recorded_by, recorded_at=_now(), notes=notes
        ))
        db.commit()
        return True, "Student checked in."
    finally:
        db.close()


def check_out_student(student_id: str, recorded_by: str, notes: str = "") -> tuple[bool, str]:
    db = get_session()
    try:
        db.add(StudentCheckRecord(
            student_id=student_id, check_type="out", recorded_by=recorded_by, recorded_at=_now(), notes=notes
        ))
        db.commit()
        return True, "Student checked out."
    finally:
        db.close()


def list_check_records(student_id: str | None = None, limit: int = 50) -> list[StudentCheckRecord]:
    db = get_session()
    try:
        stmt = select(StudentCheckRecord).order_by(StudentCheckRecord.recorded_at.desc()).limit(limit)
        if student_id:
            stmt = stmt.where(StudentCheckRecord.student_id == student_id)
        return list(db.execute(stmt).scalars().all())
    finally:
        db.close()


# ------------------------------------------------------- pickup authorization --

def create_pickup_authorization(student_id: str, authorized_by: str, person_name: str) -> tuple[bool, str, str]:
    pin = "".join(random.choices(string.digits, k=6))
    db = get_session()
    try:
        db.add(PickupAuthorization(
            student_id=student_id, authorized_by=authorized_by,
            authorized_person_name=person_name, pin_code=pin,
        ))
        db.commit()
        return True, "Pickup authorization created.", pin
    finally:
        db.close()


def verify_pickup_pin(student_id: str, pin: str, verified_by: str) -> tuple[bool, str]:
    db = get_session()
    try:
        auth = db.execute(
            select(PickupAuthorization).where(
                PickupAuthorization.student_id == student_id,
                PickupAuthorization.pin_code == pin,
                PickupAuthorization.is_used == "no",
            )
        ).scalar_one_or_none()
        if auth is None:
            return False, "Invalid or already-used pickup PIN."
        auth.is_used = "yes"
        auth.verified_by = verified_by
        auth.verified_at = _now()
        db.commit()
        return True, f"Pickup verified for {auth.authorized_person_name}."
    finally:
        db.close()


def list_pickup_authorizations(student_id: str) -> list[PickupAuthorization]:
    db = get_session()
    try:
        return list(db.execute(
            select(PickupAuthorization).where(PickupAuthorization.student_id == student_id)
        ).scalars().all())
    finally:
        db.close()


# -------------------------------------------------------------------- visitors --

def register_visitor(full_name: str, phone_number: str, purpose: str, host_name: str,
                      recorded_by: str) -> tuple[bool, str]:
    if not full_name.strip():
        return False, "Visitor name is required."
    db = get_session()
    try:
        db.add(Visitor(
            full_name=full_name.strip(), phone_number=phone_number, purpose=purpose,
            host_name=host_name, checked_in_at=_now(), recorded_by=recorded_by,
        ))
        db.commit()
        return True, "Visitor registered and checked in."
    finally:
        db.close()


def check_out_visitor(visitor_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        visitor = db.get(Visitor, visitor_id)
        if visitor is None:
            return False, "Visitor not found."
        visitor.checked_out_at = _now()
        db.commit()
        return True, "Visitor checked out."
    finally:
        db.close()


def list_visitors(limit: int = 100) -> list[Visitor]:
    db = get_session()
    try:
        return list(db.execute(
            select(Visitor).order_by(Visitor.checked_in_at.desc()).limit(limit)
        ).scalars().all())
    finally:
        db.close()


# ------------------------------------------------------------------- incidents --

def report_incident(reported_by: str, description: str, location: str = "",
                     student_id: str | None = None, severity: str = "low") -> tuple[bool, str]:
    if not description.strip():
        return False, "Incident description is required."
    db = get_session()
    try:
        db.add(Incident(
            reported_by=reported_by, student_id=student_id, location=location,
            description=description.strip(), severity=severity,
        ))
        db.commit()
        return True, "Incident reported."
    finally:
        db.close()


def update_incident_status(incident_id: str, status: str) -> tuple[bool, str]:
    db = get_session()
    try:
        incident = db.get(Incident, incident_id)
        if incident is None:
            return False, "Incident not found."
        incident.status = status
        db.commit()
        return True, "Incident updated."
    finally:
        db.close()


def list_incidents(limit: int = 100) -> list[Incident]:
    db = get_session()
    try:
        return list(db.execute(
            select(Incident).order_by(Incident.created_at.desc()).limit(limit)
        ).scalars().all())
    finally:
        db.close()


# ----------------------------------------------------------------- movements --

def log_movement(student_id: str, destination: str, logged_by: str) -> tuple[bool, str]:
    db = get_session()
    try:
        db.add(StudentMovement(
            student_id=student_id, destination=destination, logged_by=logged_by, departed_at=_now(),
        ))
        db.commit()
        return True, "Movement logged."
    finally:
        db.close()


def return_student(movement_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        movement = db.get(StudentMovement, movement_id)
        if movement is None:
            return False, "Movement record not found."
        movement.returned_at = _now()
        db.commit()
        return True, "Student marked as returned."
    finally:
        db.close()


def list_open_movements() -> list[StudentMovement]:
    db = get_session()
    try:
        return list(db.execute(
            select(StudentMovement).where(StudentMovement.returned_at.is_(None))
        ).scalars().all())
    finally:
        db.close()


# ------------------------------------------------------------- emergency alerts --

def create_emergency_alert(created_by: str, alert_type: str, message: str) -> tuple[bool, str]:
    if not message.strip():
        return False, "Alert message is required."
    db = get_session()
    try:
        db.add(EmergencyAlert(created_by=created_by, alert_type=alert_type, message=message.strip()))
        db.commit()
        return True, "Emergency alert issued."
    finally:
        db.close()


def clear_alert(alert_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        alert = db.get(EmergencyAlert, alert_id)
        if alert is None:
            return False, "Alert not found."
        alert.alert_status = "cleared"
        db.commit()
        return True, "Alert cleared."
    finally:
        db.close()


def list_alerts(active_only: bool = False) -> list[EmergencyAlert]:
    db = get_session()
    try:
        stmt = select(EmergencyAlert).order_by(EmergencyAlert.created_at.desc())
        if active_only:
            stmt = stmt.where(EmergencyAlert.alert_status == "active")
        return list(db.execute(stmt).scalars().all())
    finally:
        db.close()


# ---------------------------------------------------------------- dashboard --

def security_dashboard_stats() -> dict:
    db = get_session()
    try:
        total_checkins = db.execute(
            select(func.count(StudentCheckRecord.id)).where(StudentCheckRecord.check_type == "in")
        ).scalar_one()
        open_incidents = db.execute(
            select(func.count(Incident.id)).where(Incident.status != "resolved")
        ).scalar_one()
        active_visitors = db.execute(
            select(func.count(Visitor.id)).where(Visitor.checked_out_at.is_(None))
        ).scalar_one()
        active_alerts = db.execute(
            select(func.count(EmergencyAlert.id)).where(EmergencyAlert.alert_status == "active")
        ).scalar_one()
        return {
            "total_checkins": total_checkins, "open_incidents": open_incidents,
            "active_visitors": active_visitors, "active_alerts": active_alerts,
        }
    finally:
        db.close()
