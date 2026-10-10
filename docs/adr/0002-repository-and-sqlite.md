# ADR 0002: Use a repository port with a SQLite adapter

- Status: Accepted
- Date: 2026-10-10

## Context

The service has to persist tasks between requests in local development and in the container. It also has to be tested without sharing a database file between developers. A production deployment of this reference project is still a single node; it does not need a hosted database to demonstrate the lifecycle.

The application service should not know which engine it is talking to. If it imports SQLAlchemy, the unit tests import SQLAlchemy, and a second storage engine becomes a rewrite.

## Decision

`TaskRepository` is a `Protocol` in the domain package. `TaskService` depends on that protocol.

`SqlAlchemyTaskRepository` is the adapter for local development, tests that care about SQL, and the container. The default URL is `sqlite:///./data/tasks.db`. The container uses `sqlite:////data/tasks.db` on a volume.

`InMemoryTaskRepository` is the second adapter. Unit tests of the service use it. It stores copies so a forgotten `save` cannot pass by mutating a shared object.

Schema setup uses `Base.metadata.create_all`. Tables are created at startup when they are missing. The columns also have `CHECK` constraints so the database repeats the domain limits.

Integration tests build a new SQLite database per test: a shared in-memory connection for the adapter tests, and a temporary file for the HTTP tests. They do not point at a developer's `data/` directory.

## Consequences

- Developers need no database server.
- SQLite serializes writes. That is acceptable for one container and a course workload.
- `create_all` does not alter an existing table. A real schema change needs a migration tool and a new ADR before anybody has data they must keep.
- The port includes `ping` so readiness can check the database through the same boundary. See the architecture note for why this is not yet a separate probe port.
- Swapping in PostgreSQL later means a new adapter and a new URL. It does not mean editing `TaskService`.

## Alternatives considered

- Raw `sqlite3` calls in the service. Fewer concepts, and the SQL becomes impossible to replace or to unit test without a file.
- PostgreSQL in Compose as the only database. More realistic operations, and a heavier first run than the course needs. The port leaves that option open.
- Alembic from day one. Right for a schema that already has data. Premature while every environment can recreate the file.
