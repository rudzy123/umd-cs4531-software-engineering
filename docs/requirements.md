# Requirements

This document is the product contract for the task API. A change that disagrees with it is either a bug or a reviewed change to this file.

## Problem

Students and operators need a small, reliable way to record units of work, mark priority and completion, and filter the list. The course also needs one repository that shows how those behaviors are specified, built, tested, and released.

## Users

- A client application that stores and queries tasks over HTTP.
- An operator who needs to know whether the process should receive traffic.
- A maintainer who changes the code and has to prove the change.

## User stories

### US-1 Create a task

As a client, I can create a task with a title, an optional description, and a priority, so that work is recorded once.

Acceptance criteria:

- `POST /tasks` with a valid body returns `201` and the created task.
- The response includes `id`, `title`, `description`, `priority`, `status`, `created_at`, and `updated_at`.
- The response `Location` header is `/tasks/{id}`.
- A new task has status `open`.
- Priority defaults to `medium` when it is omitted.
- Title and description are stripped of surrounding whitespace before they are stored.
- A missing, blank, or over-long title is rejected with `422` and error code `validation_error`.
- A description longer than 2000 characters is rejected the same way.
- Fields the contract does not define are rejected. They are not ignored.

### US-2 Read tasks

As a client, I can list tasks and open one by id, so that I can see recorded work.

Acceptance criteria:

- `GET /tasks` returns a JSON array of tasks ordered by creation time, then id.
- `GET /tasks/{id}` returns that task.
- An unknown id returns `404` and error code `not_found`.
- An id that is not a UUID returns `422`.

### US-3 Filter tasks

As a client, I can filter the list by priority, completion, or both, so that I can focus on a subset.

Acceptance criteria:

- `priority` accepts only `low`, `medium`, and `high`.
- `status` accepts only `open` and `completed`.
- Supplying both filters returns the intersection.
- An unknown filter value returns `422` and names the query field in `details`.
- A filter with no matches returns an empty array, not an error.

### US-4 Update priority and completion

As a client, I can change a task's text, priority, or completion state, so that the record stays current.

Acceptance criteria:

- `PATCH /tasks/{id}` changes only the fields included in the body.
- An empty object is a successful no-op and does not move `updated_at`.
- `status: "completed"` and `status: "open"` set the completion state.
- Repeating the current status or priority does not move `updated_at`.
- Explicit `null` for a field is rejected. Omission means "leave it alone"; `null` is not a clear operation.
- An unknown task returns `404`.

### US-5 Delete a task

As a client, I can delete a task, so that abandoned work leaves the list.

Acceptance criteria:

- `DELETE /tasks/{id}` returns `204` and an empty body.
- A later read of that id returns `404`.
- Deleting an id that does not exist returns `404`.

### US-6 Operate the process

As an operator, I can ask whether the process is alive and whether it can use its database, so that a scheduler can restart or stop sending traffic.

Acceptance criteria:

- `GET /health` returns `200` and `{"status": "ok"}` without querying tasks.
- `GET /ready` returns `200` and `{"status": "ready", "database": "ok"}` when `SELECT 1` succeeds.
- When the database probe fails, `GET /ready` returns `503` and error code `not_ready`.
- The container image defines a Docker health check that calls `/health`.

### US-7 Handle failure the same way every time

As a client, I receive one error shape for every failure, so that I can handle errors without special cases per endpoint.

Acceptance criteria:

- Every error body has exactly the keys `error`, `message`, and `details`.
- `details` is either `null` or a list of `{field, message}` objects.
- Unexpected exceptions return `500`, error code `internal_error`, and a fixed message. The response does not include the exception text or a traceback.
- Unknown routes and unsupported methods use the same envelope.

## Shared rules

- The service has no authentication. Do not treat that as a reason to log request bodies.
- Timestamps are UTC.
- Identifiers are UUID strings.
- The list endpoint is not paginated. Changing its JSON shape is a breaking change.

## Out of scope

- Accounts, authorization, and multi-user ownership.
- Pagination, search, and sorting chosen by the client.
- File attachments, comments, and due dates.
- Online schema migration of existing production data.

## Definition of ready

A story is ready to build when all of the following are true:

- The user outcome is written from the caller's point of view.
- Acceptance criteria are observable through HTTP, a log line, or a test.
- The criteria name the status code and error code for each rejected case.
- Dependencies on an unpublished decision are either already accepted as an ADR or explicitly deferred.
- The story fits in one pull request, or it has been split until it does.
- Out-of-scope behavior is named, so the implementer does not invent it.

## Definition of done

A story is done when all of the following are true:

- The acceptance criteria pass in automated tests.
- Domain rules are enforced in the domain model, not only in the route.
- New failure paths use the shared error envelope.
- `make check` passes: Ruff, mypy, and pytest.
- The change follows the review checklist in [release-process.md](release-process.md).
- User-visible behavior is reflected in the README or the changelog.
- No secret, database file, or `.env` is part of the change.
- The pull request names how the change would be rolled back if it misbehaves after release.

## Traceability

| Story | Tests |
| --- | --- |
| US-1 | `tests/unit/test_domain.py`, `tests/unit/test_task_service.py`, `tests/integration/test_api.py::test_task_lifecycle` |
| US-2 | `tests/integration/test_api.py::test_task_lifecycle` |
| US-3 | `tests/unit/test_task_service.py::test_list_filters_by_priority_and_status`, `tests/integration/test_api.py::test_filters_return_only_matches` |
| US-4 | `tests/unit/test_task_service.py`, `tests/integration/test_api.py::test_task_lifecycle` |
| US-5 | `tests/unit/test_task_service.py::test_delete_removes_the_task`, `tests/integration/test_persistence.py` |
| US-6 | `tests/integration/test_api.py` health and readiness tests, Docker `HEALTHCHECK` |
| US-7 | `tests/unit/test_errors.py`, `tests/integration/test_api.py` error tests |
