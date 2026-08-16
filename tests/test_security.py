from services import people_service, security_service


def _make_student():
    people_service.create_student("Tunde", "Okoro", "ADM200")
    return people_service.list_students(search="ADM200")[0]["id"]


def test_check_in_and_out_recorded():
    student_id = _make_student()
    ok, message = security_service.check_in_student(student_id, "guard-1")
    assert ok, message
    ok, message = security_service.check_out_student(student_id, "guard-1")
    assert ok, message

    records = security_service.list_check_records(student_id)
    assert len(records) == 2


def test_pickup_pin_verification_flow():
    student_id = _make_student()
    ok, message, pin = security_service.create_pickup_authorization(student_id, "parent-1", "Aunty Ify")
    assert ok, message
    assert len(pin) == 6

    ok, verify_message = security_service.verify_pickup_pin(student_id, pin, "guard-1")
    assert ok, verify_message

    # Reusing the same PIN must fail -- it has already been consumed.
    ok2, verify_message2 = security_service.verify_pickup_pin(student_id, pin, "guard-1")
    assert not ok2
    assert "invalid" in verify_message2.lower()


def test_incident_reporting_and_status_update():
    student_id = _make_student()
    ok, message = security_service.report_incident("staff-1", "Minor scrape on playground", "Playground", student_id, "low")
    assert ok, message

    incidents = security_service.list_incidents()
    assert len(incidents) == 1
    assert incidents[0].status == "open"

    ok2, message2 = security_service.update_incident_status(incidents[0].id, "resolved")
    assert ok2, message2

    updated = security_service.list_incidents()
    assert updated[0].status == "resolved"


def test_emergency_alert_lifecycle():
    ok, message = security_service.create_emergency_alert("admin-1", "fire", "Evacuate building A")
    assert ok, message

    active_alerts = security_service.list_alerts(active_only=True)
    assert len(active_alerts) == 1

    security_service.clear_alert(active_alerts[0].id)
    active_alerts_after = security_service.list_alerts(active_only=True)
    assert len(active_alerts_after) == 0
