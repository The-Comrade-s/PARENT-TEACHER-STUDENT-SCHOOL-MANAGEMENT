from services import auth_service, school_service, teacher_service


def _make_approved_teacher(email="t1@example.com"):
    auth_service.seed_roles_and_admin()
    auth_service.register_teacher("Ada", "Lovelace", email, "GoodPass123", None)
    pending = teacher_service.list_pending_teachers()
    profile_id = next(p["teacher_profile_id"] for p in pending if p["email"] == email)
    admin_user, _ = auth_service.authenticate("admin@ptms.local", "ChangeMe123!")
    teacher_service.approve_teacher(profile_id, admin_user.id, assign_requested_class=False)
    return profile_id


def test_class_teacher_assignment_is_single_source_of_truth():
    school_service.create_class("JSS 1A", "JSS1", 40)
    school_service.create_class("JSS 1B", "JSS1", 40)
    classes = {c.name: c.id for c in school_service.list_all_classes()}

    teacher_profile_id = _make_approved_teacher()

    ok, message = teacher_service.assign_class_teacher(teacher_profile_id, classes["JSS 1A"])
    assert ok, message

    all_classes = {c.id: c for c in school_service.list_all_classes()}
    assert all_classes[classes["JSS 1A"]].class_teacher_id == teacher_profile_id
    assert all_classes[classes["JSS 1B"]].class_teacher_id is None


def test_reassigning_teacher_removes_previous_class():
    school_service.create_class("JSS 2A", "JSS2", 40)
    school_service.create_class("JSS 2B", "JSS2", 40)
    classes = {c.name: c.id for c in school_service.list_all_classes()}

    teacher_profile_id = _make_approved_teacher(email="t2@example.com")

    teacher_service.assign_class_teacher(teacher_profile_id, classes["JSS 2A"])
    teacher_service.assign_class_teacher(teacher_profile_id, classes["JSS 2B"])

    all_classes = {c.id: c for c in school_service.list_all_classes()}
    assert all_classes[classes["JSS 2A"]].class_teacher_id is None
    assert all_classes[classes["JSS 2B"]].class_teacher_id == teacher_profile_id


def test_teacher_approval_assigns_requested_class():
    auth_service.seed_roles_and_admin()
    school_service.create_class("JSS 3A", "JSS3", 40)
    class_id = school_service.list_all_classes()[0].id

    auth_service.register_teacher("Grace", "Hopper", "grace@example.com", "GoodPass123", class_id)
    pending = teacher_service.list_pending_teachers()
    entry = next(p for p in pending if p["email"] == "grace@example.com")
    assert entry["requested_class_id"] == class_id

    admin_user, _ = auth_service.authenticate("admin@ptms.local", "ChangeMe123!")
    ok, message = teacher_service.approve_teacher(entry["teacher_profile_id"], admin_user.id)
    assert ok, message

    updated_class = next(c for c in school_service.list_all_classes() if c.id == class_id)
    assert updated_class.class_teacher_id == entry["teacher_profile_id"]
