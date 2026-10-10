from pathlib import Path

from fixtures import make_blank_pptx, make_pdf, make_pptx


def upload(client, lecture_id: int, filename: str, payload: bytes):
    return client.post(
        f"/api/v1/lectures/{lecture_id}/materials",
        files={"file": (filename, payload)},
    )


def add_lecture(client, course_id: int, title: str) -> dict:
    response = client.post(
        f"/api/v1/courses/{course_id}/lectures", json={"title": title}
    )
    assert response.status_code == 201
    return response.json()


# --- happy paths ------------------------------------------------------------


def test_upload_txt_becomes_ready_with_one_segment(client, course):
    lecture = add_lecture(client, course["id"], "DNS")
    response = upload(client, lecture["id"], "notes.txt", b"DNS maps names to IPs.")
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["file_type"] == "txt"
    assert body["original_filename"] == "notes.txt"
    assert body["segment_count"] == 1
    assert body["error_message"] is None


def test_upload_pdf_keeps_page_numbers_in_segments(client, course):
    lecture = add_lecture(client, course["id"], "Transport Layer")
    response = upload(
        client,
        lecture["id"],
        "tcp.pdf",
        make_pdf(["UDP is connectionless", "TCP adds reliability"]),
    )
    assert response.status_code == 201
    assert response.json()["status"] == "ready"

    segments = client.get(f"/api/v1/materials/{response.json()['id']}/segments").json()
    assert [s["page_number"] for s in segments] == [1, 2]
    assert "TCP adds reliability" in segments[1]["text"]


def test_upload_pptx_extracts_slide_text(client, course):
    lecture = add_lecture(client, course["id"], "DNS")
    payload = make_pptx([["DNS Basics", "names map to IPs"], ["DNS Records", "A, AAAA, CNAME"]])
    response = upload(client, lecture["id"], "dns.pptx", payload)
    assert response.status_code == 201
    assert response.json()["status"] == "ready"
    assert response.json()["segment_count"] == 2


def test_notes_material_is_ready(client, course):
    lecture = add_lecture(client, course["id"], "Routing")
    response = client.post(
        f"/api/v1/lectures/{lecture['id']}/notes",
        json={"title": "Class notes", "content": "Distance vector protocols"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["kind"] == "notes"
    assert body["file_type"] == "notes"
    assert body["status"] == "ready"
    assert body["original_filename"] is None
    assert body["file_size"] == len(b"Distance vector protocols")


def test_legacy_ppt_extension_accepted_but_fails_with_actionable_error(client, course):
    lecture = add_lecture(client, course["id"], "DNS")
    response = upload(client, lecture["id"], "old.ppt", b"not really a ppt file")
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert ".pptx" in body["error_message"]


# --- validation -------------------------------------------------------------


def test_unsupported_file_type_rejected(client, course):
    lecture = add_lecture(client, course["id"], "DNS")
    response = upload(client, lecture["id"], "slides.docx", b"docx payload")
    assert response.status_code == 422
    assert "Unsupported file type" in response.json()["detail"]


def test_empty_file_rejected(client, course):
    lecture = add_lecture(client, course["id"], "DNS")
    response = upload(client, lecture["id"], "empty.txt", b"")
    assert response.status_code == 422
    assert "empty" in response.json()["detail"]


def test_oversized_file_rejected(client, course, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "max_material_bytes", 64)
    lecture = add_lecture(client, course["id"], "DNS")
    response = upload(client, lecture["id"], "big.txt", b"x" * 65)
    assert response.status_code == 413
    assert "limit" in response.json()["detail"]


def test_upload_to_unknown_lecture_404(client, course):
    response = upload(client, 99999, "x.txt", b"content")
    assert response.status_code == 404


def test_notes_with_blank_content_rejected(client, course):
    lecture = add_lecture(client, course["id"], "Routing")
    response = client.post(
        f"/api/v1/lectures/{lecture['id']}/notes", json={"title": "t", "content": "   "}
    )
    assert response.status_code == 422


# --- malformed inputs land in FAILED, nothing else breaks --------------------


def test_malformed_pdf_stored_as_failed(client, course):
    lecture = add_lecture(client, course["id"], "Security")
    response = upload(client, lecture["id"], "broken.pdf", b"this is not a pdf")
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert body["error_message"]
    assert body["segment_count"] == 0


def test_pdf_without_extractable_text_fails_as_scanned(client, course):
    lecture = add_lecture(client, course["id"], "Security")
    blank_pdf = make_pdf([""])  # one page, no text -> nothing extractable
    response = upload(client, lecture["id"], "scanned.pdf", blank_pdf)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert "scanned" in body["error_message"]


def test_pptx_without_text_fails(client, course):
    lecture = add_lecture(client, course["id"], "Security")
    response = upload(client, lecture["id"], "blank.pptx", make_blank_pptx(2))
    assert response.status_code == 201
    assert response.json()["status"] == "failed"


def test_failed_material_does_not_affect_lecture_or_other_materials(client, course):
    lecture = add_lecture(client, course["id"], "Security")
    ok = upload(client, lecture["id"], "good.txt", b"Good content")
    bad = upload(client, lecture["id"], "broken.pdf", b"not a pdf")
    assert ok.json()["status"] == "ready"
    assert bad.json()["status"] == "failed"

    lecture_response = client.get(f"/api/v1/courses/{course['id']}")
    lectures = lecture_response.json()["lectures"]
    assert lectures[0]["title"] == "Security"

    materials = client.get(f"/api/v1/lectures/{lecture['id']}/materials").json()
    assert [m["status"] for m in materials] == ["ready", "failed"]


# --- duplicates --------------------------------------------------------------


def test_duplicate_file_upload_same_lecture_conflict(client, course):
    lecture = add_lecture(client, course["id"], "DNS")
    first = upload(client, lecture["id"], "dns.txt", b"DNS maps names to IPs.")
    second = upload(client, lecture["id"], "renamed.txt", b"DNS maps names to IPs.")
    assert first.status_code == 201
    assert second.status_code == 409
    assert "already" in second.json()["detail"]


def test_same_file_in_different_lecture_is_allowed(client, course):
    l1 = add_lecture(client, course["id"], "DNS")
    l2 = add_lecture(client, course["id"], "Routing")
    payload = b"Shared excerpt for testing"
    assert upload(client, l1["id"], "shared.txt", payload).status_code == 201
    assert upload(client, l2["id"], "shared.txt", payload).status_code == 201


def test_duplicate_notes_conflict(client, course):
    lecture = add_lecture(client, course["id"], "Routing")
    payload = {"title": "Notes v1", "content": "Same content"}
    assert client.post(f"/api/v1/lectures/{lecture['id']}/notes", json=payload).status_code == 201
    repeat = client.post(
        f"/api/v1/lectures/{lecture['id']}/notes",
        json={"title": "Notes v2", "content": "Same content"},
    )
    assert repeat.status_code == 409


# --- traceability & listing ---------------------------------------------------


def test_filename_sanitized_for_storage(client, course):
    lecture = add_lecture(client, course["id"], "DNS")
    response = upload(client, lecture["id"], "../../evil name?.txt", b"content")
    assert response.status_code == 201
    body = response.json()
    assert "/" not in body["original_filename"]
    assert "\\" not in body["original_filename"]
    assert body["original_filename"].endswith(".txt")


def test_list_materials_ordered_and_typed(client, course):
    lecture = add_lecture(client, course["id"], "DNS")
    upload(client, lecture["id"], "a.txt", b"first file")
    client.post(
        f"/api/v1/lectures/{lecture['id']}/notes", json={"title": "typed", "content": "second"}
    )
    materials = client.get(f"/api/v1/lectures/{lecture['id']}/materials").json()
    assert [m["file_type"] for m in materials] == ["txt", "notes"]
    assert all("storage_path" not in m and "content_hash" not in m for m in materials)


def test_get_material_and_segments_of_unknown_material_404(client, course):
    assert client.get("/api/v1/materials/99999").status_code == 404
    assert client.get("/api/v1/materials/99999/segments").status_code == 404


def test_segments_have_sequential_positions(client, course):
    lecture = add_lecture(client, course["id"], "Transport")
    material = upload(client, lecture["id"], "t.pdf", make_pdf(["one", "two", "three"])).json()
    segments = client.get(f"/api/v1/materials/{material['id']}/segments").json()
    assert [s["position"] for s in segments] == [0, 1, 2]


# --- deletion & cascade -------------------------------------------------------


def test_delete_material_removes_row_and_stored_file(client, course):
    lecture = add_lecture(client, course["id"], "DNS")
    material = upload(client, lecture["id"], "dns.txt", b"DNS maps names to IPs.").json()

    from app.config import get_settings

    stored = Path(get_settings().materials_dir) / f"{material['id']}" / "dns.txt"
    assert stored.exists()

    assert client.delete(f"/api/v1/materials/{material['id']}").status_code == 204
    assert not stored.exists()
    assert client.get(f"/api/v1/materials/{material['id']}").status_code == 404
    assert client.get(f"/api/v1/lectures/{lecture['id']}/materials").json() == []


def test_deleting_lecture_cascades_to_materials(client, course, db_session):
    from app.models import LectureMaterial

    lecture = add_lecture(client, course["id"], "DNS")
    upload(client, lecture["id"], "dns.txt", b"DNS maps names to IPs.")
    assert client.delete(f"/api/v1/lectures/{lecture['id']}").status_code == 204
    assert db_session.query(LectureMaterial).count() == 0


def test_deleting_course_cascades_to_materials(client, course, db_session):
    from app.models import LectureMaterial

    lecture = add_lecture(client, course["id"], "DNS")
    upload(client, lecture["id"], "dns.txt", b"DNS maps names to IPs.")
    assert client.delete(f"/api/v1/courses/{course['id']}").status_code == 204
    assert db_session.query(LectureMaterial).count() == 0


# --- relationship chain --------------------------------------------------------


def test_course_lecture_material_relationship_chain(client, course, db_session):
    from app.models import Course

    lecture = add_lecture(client, course["id"], "DNS")
    material = upload(client, lecture["id"], "dns.txt", b"DNS maps names to IPs.").json()

    db_session.expire_all()
    course_obj = db_session.get(Course, course["id"])
    lecture_obj = course_obj.lectures[0]
    assert lecture_obj.materials[0].id == material["id"]
    assert lecture_obj.materials[0].lecture.title == "DNS"
