# ADR 0003: Compose the app with FastAPI dependencies

- Status: Accepted
- Date: 2026-10-10

## Context

Something has to construct the settings, the engine, the session, the repository, and the service. If each route constructs them, tests cannot replace the database without editing the route, and the layering rule from ADR 0001 becomes a comment.

A service locator or a global session would also work, and both hide the dependency. A reader cannot see what a route needs from its signature.

## Decision

FastAPI's `Depends` is the composition mechanism.

- `create_app(settings)` builds the process. Tests pass a `Settings` instance. The server process uses the environment.
- The lifespan opens the engine, creates tables, and stores the session factory on `app.state`.
- `get_session` yields a session and commits when the request finishes. Any exception rolls the session back and closes it.
- `get_task_repository` and `get_task_service` build the objects for one request.
- Routes annotate `ServiceDep` or `RepositoryDep`. Those aliases are the only way a route reaches storage.

`api/dependencies.py` is the composition root. It is the only module under `api/` that may import infrastructure. The architecture test enforces that exception by name.

Tests replace a dependency with `app.dependency_overrides`. The readiness failure test does this with a probe whose `ping` returns false. The route stays unchanged.

## Consequences

- A route signature shows the collaborator it uses.
- Override scope is the app object. Integration fixtures build a new app per test so overrides cannot leak.
- The composition root is allowed to know about SQLAlchemy. The rest of the HTTP package is not.
- A second process entry point, such as a worker, would need its own composition root. It should not import routes to obtain a service.

## Alternatives considered

- Constructing `SqlAlchemyTaskRepository` inside `TaskService`. The service would be easier to call and impossible to test without SQLite.
- A third-party injection container. More machinery than a six-function wiring module needs.
- Passing the repository through function arguments from `main` without `Depends`. Clear, and it fights the framework that already calls the routes.
