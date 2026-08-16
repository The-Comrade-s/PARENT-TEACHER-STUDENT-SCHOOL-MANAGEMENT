"""
Academic results and grading.

Grade bands and CA/exam weighting are configurable data (GradingSystem /
GradeBand / AssessmentConfig), never hardcoded thresholds in this module.
"""

from sqlalchemy import select

from database.connection import get_session
from models.academic import GradingSystem, GradeBand, AssessmentConfig, Result
from models.people import StudentProfile


def ensure_default_grading_setup():
    """Seeds a sensible default grading system and assessment config if none exist yet."""
    db = get_session()
    try:
        existing = db.execute(select(GradingSystem).where(GradingSystem.is_default == True)).scalar_one_or_none()  # noqa: E712
        if existing is None:
            system = GradingSystem(name="Standard Grading", is_default=True)
            db.add(system)
            db.flush()
            default_bands = [
                ("A", 70, 100, "Excellent", 5.0),
                ("B", 60, 69.99, "Very Good", 4.0),
                ("C", 50, 59.99, "Good", 3.0),
                ("D", 45, 49.99, "Fair", 2.0),
                ("E", 40, 44.99, "Pass", 1.0),
                ("F", 0, 39.99, "Fail", 0.0),
            ]
            for grade, lo, hi, remark, gp in default_bands:
                db.add(GradeBand(
                    grading_system_id=system.id, grade=grade, min_score=lo, max_score=hi,
                    remark=remark, grade_point=gp,
                ))

        existing_config = db.execute(
            select(AssessmentConfig).where(AssessmentConfig.is_default == True)  # noqa: E712
        ).scalar_one_or_none()
        if existing_config is None:
            db.add(AssessmentConfig(name="Standard", ca_weight=40, exam_weight=60, is_default=True))

        db.commit()
    finally:
        db.close()


def get_default_grading_system() -> GradingSystem | None:
    db = get_session()
    try:
        return db.execute(
            select(GradingSystem).where(GradingSystem.is_default == True)  # noqa: E712
        ).scalar_one_or_none()
    finally:
        db.close()


def compute_grade(total_score: float) -> tuple[str, str]:
    """Returns (grade, remark) using the default grading system's bands."""
    db = get_session()
    try:
        system = db.execute(
            select(GradingSystem).where(GradingSystem.is_default == True)  # noqa: E712
        ).scalar_one_or_none()
        if system is None:
            return "N/A", ""
        for band in system.bands:
            if band.min_score <= total_score <= band.max_score:
                return band.grade, band.remark or ""
        return "N/A", ""
    finally:
        db.close()


def enter_score(student_id: str, class_id: str, subject_id: str, term_id: str, teacher_id: str,
                 ca_score: float, exam_score: float) -> tuple[bool, str]:
    total = ca_score + exam_score
    grade, remark = compute_grade(total)

    db = get_session()
    try:
        existing = db.execute(
            select(Result).where(
                Result.student_id == student_id, Result.subject_id == subject_id, Result.term_id == term_id
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(Result(
                student_id=student_id, class_id=class_id, subject_id=subject_id, term_id=term_id,
                teacher_id=teacher_id, ca_score=ca_score, exam_score=exam_score, total_score=total,
                grade=grade, remark=remark, status="draft",
            ))
        else:
            existing.ca_score = ca_score
            existing.exam_score = exam_score
            existing.total_score = total
            existing.grade = grade
            existing.remark = remark
            existing.status = "draft"
        db.commit()
        return True, "Score saved."
    finally:
        db.close()


def submit_results_for_review(class_id: str, subject_id: str, term_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        results = db.execute(
            select(Result).where(
                Result.class_id == class_id, Result.subject_id == subject_id, Result.term_id == term_id
            )
        ).scalars().all()
        for r in results:
            if r.status == "draft":
                r.status = "submitted"
        db.commit()
        return True, "Results submitted for review."
    finally:
        db.close()


def publish_results(class_id: str, term_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        results = db.execute(
            select(Result).where(Result.class_id == class_id, Result.term_id == term_id)
        ).scalars().all()
        for r in results:
            if r.status in ("submitted", "reviewed"):
                r.status = "published"
        db.commit()
        return True, "Results published."
    finally:
        db.close()


def get_class_results(class_id: str, subject_id: str, term_id: str) -> list[dict]:
    db = get_session()
    try:
        results = db.execute(
            select(Result).where(
                Result.class_id == class_id, Result.subject_id == subject_id, Result.term_id == term_id
            )
        ).scalars().all()
        students = db.execute(
            select(StudentProfile).where(StudentProfile.current_class_id == class_id)
        ).scalars().all()
        results_by_student = {r.student_id: r for r in results}

        rows = []
        for s in students:
            r = results_by_student.get(s.id)
            rows.append({
                "student_id": s.id,
                "admission_number": s.admission_number,
                "ca_score": r.ca_score if r else 0,
                "exam_score": r.exam_score if r else 0,
                "total_score": r.total_score if r else 0,
                "grade": r.grade if r else "",
                "status": r.status if r else "draft",
            })
        return rows
    finally:
        db.close()


def get_student_results(student_id: str, term_id: str, published_only: bool = True) -> list[dict]:
    db = get_session()
    try:
        stmt = select(Result).where(Result.student_id == student_id, Result.term_id == term_id)
        if published_only:
            stmt = stmt.where(Result.status == "published")
        results = db.execute(stmt).scalars().all()
        return [{
            "subject_name": r.subject.name if r.subject else "Unknown",
            "ca_score": r.ca_score, "exam_score": r.exam_score, "total_score": r.total_score,
            "grade": r.grade, "remark": r.remark,
        } for r in results]
    finally:
        db.close()
