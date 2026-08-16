"""Assignment management and submission tracking."""

from sqlalchemy import select

from database.connection import get_session
from models.academic import Assignment, AssignmentSubmission
from models.people import StudentProfile


def create_assignment(class_id: str, teacher_id: str, title: str, description: str = "",
                       subject_id: str | None = None, due_date=None) -> tuple[bool, str]:
    if not title.strip():
        return False, "Assignment title is required."
    db = get_session()
    try:
        assignment = Assignment(
            class_id=class_id, teacher_id=teacher_id, title=title.strip(),
            description=description, subject_id=subject_id, due_date=due_date,
        )
        db.add(assignment)
        db.flush()

        students = db.execute(
            select(StudentProfile).where(
                StudentProfile.current_class_id == class_id, StudentProfile.student_status == "active"
            )
        ).scalars().all()
        for s in students:
            db.add(AssignmentSubmission(assignment_id=assignment.id, student_id=s.id))
        db.commit()
        return True, "Assignment created."
    finally:
        db.close()


def update_assignment(assignment_id: str, title: str, description: str, due_date=None) -> tuple[bool, str]:
    db = get_session()
    try:
        a = db.get(Assignment, assignment_id)
        if a is None:
            return False, "Assignment not found."
        a.title = title.strip()
        a.description = description
        a.due_date = due_date
        db.commit()
        return True, "Assignment updated."
    finally:
        db.close()


def delete_assignment(assignment_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        a = db.get(Assignment, assignment_id)
        if a is None:
            return False, "Assignment not found."
        db.delete(a)
        db.commit()
        return True, "Assignment deleted."
    finally:
        db.close()


def list_assignments_for_class(class_id: str) -> list[Assignment]:
    db = get_session()
    try:
        return list(db.execute(
            select(Assignment).where(Assignment.class_id == class_id).order_by(Assignment.due_date)
        ).scalars().all())
    finally:
        db.close()


def list_assignments_for_teacher(teacher_id: str) -> list[Assignment]:
    db = get_session()
    try:
        return list(db.execute(
            select(Assignment).where(Assignment.teacher_id == teacher_id).order_by(Assignment.due_date)
        ).scalars().all())
    finally:
        db.close()


def list_assignments_for_student(student_id: str, class_id: str) -> list[dict]:
    db = get_session()
    try:
        assignments = db.execute(select(Assignment).where(Assignment.class_id == class_id)).scalars().all()
        results = []
        for a in assignments:
            submission = db.execute(
                select(AssignmentSubmission).where(
                    AssignmentSubmission.assignment_id == a.id, AssignmentSubmission.student_id == student_id
                )
            ).scalar_one_or_none()
            results.append({
                "id": a.id, "title": a.title, "description": a.description, "due_date": a.due_date,
                "submission_status": submission.submitted_at_status if submission else "not_submitted",
                "score": submission.score if submission else None,
                "submission_id": submission.id if submission else None,
            })
        return results
    finally:
        db.close()


def submit_assignment(submission_id: str, submission_text: str) -> tuple[bool, str]:
    db = get_session()
    try:
        s = db.get(AssignmentSubmission, submission_id)
        if s is None:
            return False, "Submission record not found."
        s.submission_text = submission_text
        s.submitted_at_status = "submitted"
        db.commit()
        return True, "Assignment submitted."
    finally:
        db.close()


def review_submission(submission_id: str, score: float, feedback: str = "") -> tuple[bool, str]:
    db = get_session()
    try:
        s = db.get(AssignmentSubmission, submission_id)
        if s is None:
            return False, "Submission record not found."
        s.score = score
        s.teacher_feedback = feedback
        s.submitted_at_status = "reviewed"
        db.commit()
        return True, "Submission reviewed."
    finally:
        db.close()


def list_submissions_for_assignment(assignment_id: str) -> list[dict]:
    db = get_session()
    try:
        subs = db.execute(
            select(AssignmentSubmission).where(AssignmentSubmission.assignment_id == assignment_id)
        ).scalars().all()
        results = []
        for s in subs:
            student = db.get(StudentProfile, s.student_id)
            results.append({
                "submission_id": s.id,
                "student_admission_number": student.admission_number if student else "Unknown",
                "status": s.submitted_at_status,
                "score": s.score,
            })
        return results
    finally:
        db.close()
