from datetime import date

from services import people_service, school_service, attendance_service, results_service, auth_service


def _setup_class_with_student():
    school_service.create_class("JSS 1C", "JSS1", 40)
    class_id = school_service.list_all_classes()[0].id
    people_service.create_student("Ngozi", "Bello", "ADM100", class_id=class_id)
    student = people_service.list_students(search="ADM100")[0]
    return class_id, student["id"]


def test_attendance_save_and_lock_prevents_edits():
    class_id, student_id = _setup_class_with_student()
    today = date.today()

    ok, message = attendance_service.save_attendance(class_id, today, {student_id: "present"}, marked_by="tester")
    assert ok, message

    ok, message = attendance_service.lock_attendance(class_id, today)
    assert ok, message

    ok, message = attendance_service.save_attendance(class_id, today, {student_id: "absent"}, marked_by="tester")
    assert not ok
    assert "locked" in message.lower()

    ok, message = attendance_service.reopen_attendance(class_id, today)
    assert ok, message

    ok, message = attendance_service.save_attendance(class_id, today, {student_id: "absent"}, marked_by="tester")
    assert ok, message


def test_grading_computes_correct_band():
    results_service.ensure_default_grading_setup()
    grade, remark = results_service.compute_grade(75)
    assert grade == "A"

    grade, remark = results_service.compute_grade(42)
    assert grade == "E"

    grade, remark = results_service.compute_grade(10)
    assert grade == "F"


def test_enter_score_and_publish_workflow():
    results_service.ensure_default_grading_setup()
    class_id, student_id = _setup_class_with_student()
    school_service.create_subject("Mathematics", "MTH101")
    subject_id = school_service.list_subjects()[0].id
    school_service.create_session("2025/2026")
    session_id = school_service.list_sessions()[0].id
    school_service.create_term(session_id, "First Term")
    term = school_service.list_terms()[0]
    school_service.activate_term(term.id)

    ok, message = results_service.enter_score(student_id, class_id, subject_id, term.id, "teacher-1", 35, 50)
    assert ok, message

    rows = results_service.get_class_results(class_id, subject_id, term.id)
    row = next(r for r in rows if r["student_id"] == student_id)
    assert row["total_score"] == 85
    assert row["grade"] == "A"
    assert row["status"] == "draft"

    results_service.submit_results_for_review(class_id, subject_id, term.id)
    results_service.publish_results(class_id, term.id)

    published = results_service.get_student_results(student_id, term.id, published_only=True)
    assert len(published) == 1
    assert published[0]["grade"] == "A"
