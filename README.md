# Task API

Reference project for CS 4531. It is a small task-management HTTP API built the way a team would actually ship it: a domain model, an application service, a persistence port, a replaceable adapter, automated checks, and the documents a team uses to decide, test, and release.

The service lets a client create, read, update, delete, and filter tasks. It validates input, returns one error shape for every failure, and exposes health and readiness endpoints for an operator.

## Start here

Read [docs/learning-log.md](docs/learning-log.md) once, then use the map below when you need a specific practice.

| Question | Document |
| --- | --- |
| What should the system do? | [docs/requirements.md](docs/requirements.md) |
| How is the code divided, and why? | [docs/architecture.md](docs/architecture.md) |
| Why were these tradeoffs chosen? | [docs/adr](docs/adr/README.md) |
| What is tested, and at which layer? | [docs/testing-strategy.md](docs/testing-strategy.md) |
| How does a change reach production, and how do we undo it? | [docs/release-process.md](docs/release-process.md) |

## Requirements

- Python 3.12
- The tools in `pyproject.toml`: FastAPI, Pydantic, SQLAlchemy, pytest, Ruff, and mypy

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

`make install` does the same thing. Copy `.env.example` to `.env` only when you want local overrides. The application starts with safe defaults, and `.env` is gitignored.

## Run

```bash
make run
```

The API listens on `http://127.0.0.1:8000`. Interactive docs are at `/docs`.

Create a task:

```bash
curl -s -X POST http://127.0.0.1:8000/tasks \
  -H 'content-type: application/json' \
  -d '{"title":"Draft the ADR","description":"Record the options","priority":"high"}'
```

Mark it complete:

```bash
curl -s -X PATCH http://127.0.0.1:8000/tasks/<task-id> \
  -H 'content-type: application/json' \
  -d '{"status":"completed"}'
```

List open high-priority tasks:

```bash
curl -s 'http://127.0.0.1:8000/tasks?status=open&priority=high'
```

## HTTP API

| Method | Path | Result |
| --- | --- | --- |
| `GET` | `/health` | Process is running |
| `GET` | `/ready` | Process can reach the database |
| `POST` | `/tasks` | Create a task. New tasks start `open` |
| `GET` | `/tasks` | List tasks. Optional `priority` and `status` filters |
| `GET` | `/tasks/{id}` | Read one task |
| `PATCH` | `/tasks/{id}` | Change title, description, priority, or completion |
| `DELETE` | `/tasks/{id}` | Remove a task |

`priority` is `low`, `medium`, or `high`. `status` is `open` or `completed`. Titles are required, stripped, and limited to 200 characters. Descriptions are limited to 2000 characters. Unknown JSON fields are rejected.

Every error uses the same body:

```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": [{ "field": "title", "message": "String should have at least 1 character" }]
}
```

`details` is `null` when the failure has no field list. Clients should branch on `error` and the HTTP status, not on prose.

| Status | `error` | When |
| --- | --- | --- |
| 404 | `not_found` | Unknown task or route |
| 405 | `method_not_allowed` | Verb not implemented for that path |
| 409 | `conflict` | Insert collides with an existing id |
| 422 | `validation_error` or `invalid_task` | The request or a domain rule rejected the data |
| 500 | `internal_error` | Unexpected failure. The body does not include the exception |
| 503 | `not_ready` | The database probe failed |

`/health` answers without touching the database. `/ready` runs `SELECT 1`. A failed probe means the process should not receive traffic.

## Configuration

Settings load from the environment, then from an optional `.env` file. Names use the `TASK_API_` prefix. Nothing secret is committed.

| Variable | Default | Purpose |
| --- | --- | --- |
| `TASK_API_ENVIRONMENT` | `local` | Reported in the startup log |
| `TASK_API_LOG_LEVEL` | `INFO` | Root log level |
| `TASK_API_DATABASE_URL` | `sqlite:///./data/tasks.db` | SQLAlchemy URL |

Logs are one JSON object per line. A request log includes the method, path, status, duration, and request id. It does not include the body. Send `x-request-id` to correlate a call; otherwise the service generates one and returns it.

## Quality gates

```bash
make check   # ruff, mypy, pytest
make build   # docker image
make smoke   # start the image and call GET /health
```

`make ci` runs the checks and the image build. GitHub Actions runs lint, type check, test, and image build as separate jobs. The build job also calls `/health`.

## Container

```bash
docker compose up --build
```

The image runs as a non-root user, stores SQLite at `/data/tasks.db`, and defines a Docker `HEALTHCHECK` against `/health`. Compose mounts a volume at `/data` so the file survives a restart.

## Layout

```text
src/task_api/
  domain/            Task rules and the repository port
  application/       Use cases
  infrastructure/    Settings, logging, SQLite, in-memory adapter
  api/               Schemas, routes, errors, and the composition root
tests/unit/          Domain, service, logging, and import rules
tests/integration/   SQLite and HTTP
```

`api/dependencies.py` is the only HTTP module allowed to import the database. An automated test keeps it that way.

## Versioning

The package version is `0.1.0`. Releases use [semantic versioning](https://semver.org). Commits use [Conventional Commits](https://www.conventionalcommits.org). The commit that introduces this tree is recorded in [COMMIT_MESSAGE.md](COMMIT_MESSAGE.md). Release steps, the branching model, the review checklist, and rollback are in [docs/release-process.md](docs/release-process.md).

## Intentionally out of scope

Authentication, pagination, background workers, and schema migrations are not implemented. Each one would change the contract or the operations story, and adding them later is a reviewed design decision rather than a silent patch. The list endpoint returns a JSON array; adding page metadata later is a breaking change.

## License

MIT. See [LICENSE](LICENSE).
