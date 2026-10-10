"""HTTP contract: validation, filters, status codes, and the error envelope."""

from typing import Any, cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from task_api.api.dependencies import get_task_repository, get_task_service
from task_api.application.services import TaskService


def test_health_is_alive_without_reading_tasks(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert _object(response) == {"status": "ok"}


def test_readiness_checks_the_database(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert _object(response) == {"status": "ready", "database": "ok"}


def test_readiness_fails_when_the_database_probe_fails(
    api_app: FastAPI,
    client: TestClient,
) -> None:
    class UnavailableDatabase:
        def ping(self) -> bool:
            return False

    api_app.dependency_overrides[get_task_repository] = lambda: UnavailableDatabase()

    response = client.get("/ready")
    body = _object(response)

    assert response.status_code == 503
    assert body["error"] == "not_ready"
    assert body["message"] == "Database is unavailable"
    assert body["details"] is None


def test_task_lifecycle(client: TestClient) -> None:
    created = client.post(
        "/tasks",
        json={
            "title": "  Draft the ADR  ",
            "description": "  capture the decision  ",
            "priority": "high",
        },
    )
    body = _object(created)

    assert created.status_code == 201
    assert created.headers["location"] == f"/tasks/{body['id']}"
    assert body["title"] == "Draft the ADR"
    assert body["description"] == "capture the decision"
    assert body["priority"] == "high"
    assert body["status"] == "open"

    fetched = client.get(f"/tasks/{body['id']}")
    assert fetched.status_code == 200
    assert _object(fetched)["title"] == "Draft the ADR"

    updated = client.patch(
        f"/tasks/{body['id']}",
        json={"priority": "low", "status": "completed"},
    )
    updated_body = _object(updated)
    assert updated.status_code == 200
    assert updated_body["priority"] == "low"
    assert updated_body["status"] == "completed"
    assert updated_body["title"] == "Draft the ADR"

    listed = client.get("/tasks", params={"status": "completed", "priority": "low"})
    matches = _list(listed)
    assert listed.status_code == 200
    assert [item["id"] for item in matches] == [body["id"]]

    removed = client.delete(f"/tasks/{body['id']}")
    assert removed.status_code == 204
    assert removed.content == b""

    missing = client.get(f"/tasks/{body['id']}")
    missing_body = _object(missing)
    assert missing.status_code == 404
    assert missing_body["error"] == "not_found"
    assert set(missing_body) == {"error", "message", "details"}


def test_filters_return_only_matches(client: TestClient) -> None:
    client.post("/tasks", json={"title": "Open high", "priority": "high"})
    client.post("/tasks", json={"title": "Open low", "priority": "low"})
    completed = _object(client.post("/tasks", json={"title": "Done", "priority": "high"}))
    client.patch(f"/tasks/{completed['id']}", json={"status": "completed"})

    open_tasks = _list(client.get("/tasks", params={"status": "open"}))
    high_tasks = _list(client.get("/tasks", params={"priority": "high"}))

    assert {item["title"] for item in open_tasks} == {"Open high", "Open low"}
    assert {item["title"] for item in high_tasks} == {"Open high", "Done"}


def test_validation_errors_share_one_envelope(client: TestClient) -> None:
    blank = client.post("/tasks", json={"title": "   "})
    extra = client.post("/tasks", json={"title": "Ok", "owner": "ada"})
    bad_query = client.get("/tasks", params={"priority": "urgent"})
    bad_id = client.get("/tasks/not-a-uuid")
    null_title = client.patch(
        "/tasks/00000000-0000-0000-0000-000000000000",
        json={"title": None},
    )

    for response in (blank, extra, bad_query, bad_id, null_title):
        body = _object(response)
        assert response.status_code == 422
        assert body["error"] == "validation_error"
        assert body["message"] == "Request validation failed"
        assert isinstance(body["details"], list)
        assert body["details"]


def test_unknown_route_and_method_use_the_same_envelope(client: TestClient) -> None:
    missing = _object(client.get("/missing"))
    wrong_method = _object(client.put("/tasks"))

    assert missing == {
        "error": "not_found",
        "message": "Not Found",
        "details": None,
    }
    assert wrong_method["error"] == "method_not_allowed"
    assert set(wrong_method) == {"error", "message", "details"}


def test_unexpected_errors_hide_internal_details(api_app: FastAPI) -> None:
    def explode() -> TaskService:
        raise RuntimeError("disk password=secret")

    api_app.dependency_overrides[get_task_service] = explode

    # The server logs the traceback and then re-raises. The client still receives
    # the generic body when it is told not to surface that server exception.
    with TestClient(api_app, raise_server_exceptions=False) as quiet_client:
        response = quiet_client.get("/tasks")
    rendered = response.text

    assert response.status_code == 500
    assert _object(response)["error"] == "internal_error"
    assert _object(response)["message"] == "An unexpected error occurred"
    assert "secret" not in rendered
    assert "Traceback" not in rendered


def test_request_id_is_echoed(client: TestClient) -> None:
    response = client.get("/health", headers={"x-request-id": "req-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-123"


def test_client_receives_a_generated_request_id(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def _object(response: Response) -> dict[str, Any]:
    body = cast(object, response.json())
    assert isinstance(body, dict)
    return cast(dict[str, Any], body)


def _list(response: Response) -> list[dict[str, Any]]:
    body = cast(object, response.json())
    assert isinstance(body, list)
    return [cast(dict[str, Any], item) for item in body]
