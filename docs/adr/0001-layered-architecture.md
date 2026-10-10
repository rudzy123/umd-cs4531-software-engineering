# ADR 0001: Split domain, application, infrastructure, and API

- Status: Accepted
- Date: 2026-10-10

## Context

The course needs one codebase that demonstrates a complete lifecycle, and the codebase has to stay small enough to read in an afternoon. A single `main.py` that validates JSON, applies rules, and writes SQL would run, and it would also teach the wrong lesson: every change would risk every other change.

The behavior itself is small. Tasks have a title, a description, a priority, and a completion state. The design has to make the rules findable when the framework changes.

## Decision

The code is divided into four layers:

- `domain` holds the `Task` aggregate, its invariants, and the repository port.
- `application` holds `TaskService` and the draft/patch objects a use case accepts.
- `infrastructure` holds settings, JSON logging, the SQLite schema, and the adapters.
- `api` holds the HTTP schema, routes, error mapping, and the composition root.

Dependencies point inward. A unit test parses imports and fails the build when that rule is broken. Domain types do not import FastAPI, Pydantic, or SQLAlchemy.

The HTTP schema may use the domain enums. Priority and status are the public vocabulary, not an accident of the database. Duplicating the enums would let the wire contract and the rule drift apart.

## Consequences

- A rule change starts in `domain/models.py` and gains a unit test that does not boot a server.
- A new database is a new adapter. The service stays put.
- The first feature takes more files than a script would. That cost is the point of the reference project.
- Someone in a hurry can still hide a rule in a route. The import test does not catch that. Review has to.

## Alternatives considered

- One module per endpoint, with SQL in the route. Faster to start, and the invariants become untestable without HTTP.
- A framework-first layout generated from a template, with empty service classes. The layers would exist as names only. This project puts a real rule and a real query in each layer so the names mean something.
