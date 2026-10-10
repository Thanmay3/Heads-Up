import pytest


def test_create_course_returns_201(client):
    response = client.post("/api/v1/courses", json={"name": "Computer Networks"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Computer Networks"
    assert isinstance(body["id"], int)
    assert body["created_at"]
    assert body["updated_at"]


def test_create_course_strips_surrounding_whitespace(client):
    response = client.post("/api/v1/courses", json={"name": "  Algorithms  "})
    assert response.status_code == 201
    assert response.json()["name"] == "Algorithms"


@pytest.mark.parametrize("name", ["", "   ", "\n\t"])
def test_create_course_rejects_blank_name(client, name):
    response = client.post("/api/v1/courses", json={"name": name})
    assert response.status_code == 422


def test_create_course_rejects_missing_name(client):
    assert client.post("/api/v1/courses", json={}).status_code == 422


def test_list_courses_empty(client):
    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    assert response.json() == []


def test_list_courses_reports_lecture_and_missed_counts(client, course):
    client.post(f"/api/v1/courses/{course['id']}/lectures", json={"title": "Introduction"})
    second = client.post(
        f"/api/v1/courses/{course['id']}/lectures", json={"title": "Congestion Control"}
    ).json()
    client.patch(f"/api/v1/lectures/{second['id']}", json={"status": "missed"})

    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    [item] = response.json()
    assert item["id"] == course["id"]
    assert item["lecture_count"] == 2
    assert item["missed_count"] == 1


def test_list_courses_orders_newest_first(client):
    first = client.post("/api/v1/courses", json={"name": "First"}).json()
    second = client.post("/api/v1/courses", json={"name": "Second"}).json()

    names = [item["name"] for item in client.get("/api/v1/courses").json()]
    assert names == ["Second", "First"]
    assert first["id"] != second["id"]


def test_course_detail_contains_lectures_and_summary(client, course):
    for title in ["Introduction", "Congestion Control", "Quality of Service"]:
        client.post(f"/api/v1/courses/{course['id']}/lectures", json={"title": title})

    response = client.get(f"/api/v1/courses/{course['id']}")
    assert response.status_code == 200
    body = response.json()
    assert [lecture["order_index"] for lecture in body["lectures"]] == [1, 2, 3]
    assert body["summary"] == {
        "last_understood_lecture": None,
        "upcoming_lecture": None,
        "missed_lectures": [],
        "unmarked_before_upcoming": [],
    }


def test_get_missing_course_returns_404(client):
    response = client.get("/api/v1/courses/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Course 999 not found"


def test_update_course_name(client, course):
    response = client.patch(f"/api/v1/courses/{course['id']}", json={"name": "Distributed Systems"})
    assert response.status_code == 200
    assert response.json()["name"] == "Distributed Systems"

    assert client.get(f"/api/v1/courses/{course['id']}").json()["name"] == "Distributed Systems"


def test_update_course_rejects_blank_name(client, course):
    response = client.patch(f"/api/v1/courses/{course['id']}", json={"name": "  "})
    assert response.status_code == 422


def test_update_missing_course_returns_404(client):
    assert client.patch("/api/v1/courses/999", json={"name": "X"}).status_code == 404


def test_delete_course_removes_it(client, course):
    assert client.delete(f"/api/v1/courses/{course['id']}").status_code == 204
    assert client.get(f"/api/v1/courses/{course['id']}").status_code == 404
    assert client.get("/api/v1/courses").json() == []


def test_delete_missing_course_returns_404(client):
    assert client.delete("/api/v1/courses/999").status_code == 404
