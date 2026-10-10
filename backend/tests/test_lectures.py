def test_add_lecture_appends_with_next_order_index(client, course):
    first = client.post(f"/api/v1/courses/{course['id']}/lectures", json={"title": "Introduction"})
    assert first.status_code == 201
    assert first.json()["order_index"] == 1
    assert first.json()["status"] == "unmarked"

    second = client.post(f"/api/v1/courses/{course['id']}/lectures", json={"title": "HTTP"})
    assert second.json()["order_index"] == 2


def test_add_lecture_to_missing_course_returns_404(client):
    response = client.post("/api/v1/courses/999/lectures", json={"title": "Ghost"})
    assert response.status_code == 404


def test_add_lecture_rejects_blank_title(client, course):
    response = client.post(f"/api/v1/courses/{course['id']}/lectures", json={"title": "   "})
    assert response.status_code == 422


def test_update_lecture_title(client, course):
    lecture = client.post(
        f"/api/v1/courses/{course['id']}/lectures", json={"title": "Congestion Contorl"}
    ).json()
    response = client.patch(
        f"/api/v1/lectures/{lecture['id']}", json={"title": "Congestion Control"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Congestion Control"


def test_update_lecture_status(client, course):
    lecture = client.post(
        f"/api/v1/courses/{course['id']}/lectures", json={"title": "Introduction"}
    ).json()
    response = client.patch(f"/api/v1/lectures/{lecture['id']}", json={"status": "understood"})
    assert response.status_code == 200
    assert response.json()["status"] == "understood"


def test_update_lecture_rejects_unknown_status(client, course):
    lecture = client.post(
        f"/api/v1/courses/{course['id']}/lectures", json={"title": "Introduction"}
    ).json()
    response = client.patch(f"/api/v1/lectures/{lecture['id']}", json={"status": "bored"})
    assert response.status_code == 422


def test_update_lecture_rejects_empty_payload(client, course):
    lecture = client.post(
        f"/api/v1/courses/{course['id']}/lectures", json={"title": "Introduction"}
    ).json()
    assert client.patch(f"/api/v1/lectures/{lecture['id']}", json={}).status_code == 422


def test_update_missing_lecture_returns_404(client):
    assert client.patch("/api/v1/lectures/999", json={"status": "missed"}).status_code == 404


def test_only_one_lecture_can_be_upcoming(client, course):
    lectures = [
        client.post(f"/api/v1/courses/{course['id']}/lectures", json={"title": title}).json()
        for title in ["Introduction", "HTTP", "Congestion Control"]
    ]
    client.patch(f"/api/v1/lectures/{lectures[0]['id']}", json={"status": "upcoming"})
    client.patch(f"/api/v1/lectures/{lectures[1]['id']}", json={"status": "upcoming"})

    detail = client.get(f"/api/v1/courses/{course['id']}").json()
    statuses = {lecture["order_index"]: lecture["status"] for lecture in detail["lectures"]}
    assert statuses == {1: "unmarked", 2: "upcoming", 3: "unmarked"}
    assert detail["summary"]["upcoming_lecture"]["order_index"] == 2


def test_re_marking_the_same_lecture_upcoming_is_idempotent(client, course):
    lecture = client.post(
        f"/api/v1/courses/{course['id']}/lectures", json={"title": "Introduction"}
    ).json()
    client.patch(f"/api/v1/lectures/{lecture['id']}", json={"status": "upcoming"})
    response = client.patch(f"/api/v1/lectures/{lecture['id']}", json={"status": "upcoming"})
    assert response.status_code == 200
    assert response.json()["status"] == "upcoming"


def test_delete_lecture_closes_order_gap(client, course):
    lectures = [
        client.post(f"/api/v1/courses/{course['id']}/lectures", json={"title": title}).json()
        for title in ["A", "B", "C", "D"]
    ]
    assert client.delete(f"/api/v1/lectures/{lectures[1]['id']}").status_code == 204

    detail = client.get(f"/api/v1/courses/{course['id']}").json()
    assert [(lecture["title"], lecture["order_index"]) for lecture in detail["lectures"]] == [
        ("A", 1),
        ("C", 2),
        ("D", 3),
    ]

    # The freed index must be reusable: a new lecture appends at 4.
    added = client.post(f"/api/v1/courses/{course['id']}/lectures", json={"title": "E"})
    assert added.json()["order_index"] == 4


def test_delete_missing_lecture_returns_404(client):
    assert client.delete("/api/v1/lectures/999").status_code == 404


def test_deleting_course_cascades_to_lectures(client, course, db_session):
    from app.models import Lecture

    client.post(f"/api/v1/courses/{course['id']}/lectures", json={"title": "Introduction"})
    client.delete(f"/api/v1/courses/{course['id']}")

    db_session.expire_all()
    assert db_session.query(Lecture).count() == 0
