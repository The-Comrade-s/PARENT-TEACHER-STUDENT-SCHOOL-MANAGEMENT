from services import people_service, auth_service, school_service


def test_create_student_and_search():
    ok, message = people_service.create_student("Ada", "Okafor", "ADM001")
    assert ok, message

    results = people_service.list_students(search="ADM001")
    assert len(results) == 1
    assert results[0]["admission_number"] == "ADM001"


def test_duplicate_admission_number_rejected():
    people_service.create_student("Ada", "Okafor", "ADM002")
    ok, message = people_service.create_student("Chidi", "Eze", "ADM002")
    assert not ok
    assert "already exists" in message


def test_student_class_reassignment():
    school_service.create_class("Primary 1", "P1", 30)
    class_id = school_service.list_all_classes()[0].id
    people_service.create_student("Bola", "Ade", "ADM003")
    student = people_service.list_students(search="ADM003")[0]

    ok, message = people_service.update_student_class(student["id"], class_id)
    assert ok, message

    updated = people_service.list_students(search="ADM003")[0]
    assert updated["class_name"] == "Primary 1"


def test_parent_child_linking():
    auth_service.seed_roles_and_admin()
    auth_service.register_parent("Femi", "Johnson", "femi@example.com", "GoodPass123")
    people_service.create_student("Kunle", "Johnson", "ADM004")

    parent = people_service.list_parents(search="femi@example.com")[0]
    student = people_service.list_students(search="ADM004")[0]

    ok, message = people_service.link_parent_to_student(parent["id"], student["id"])
    assert ok, message

    updated_parent = people_service.list_parents(search="femi@example.com")[0]
    assert updated_parent["children_count"] == 1

    ok2, message2 = people_service.link_parent_to_student(parent["id"], student["id"])
    assert not ok2
    assert "already linked" in message2
