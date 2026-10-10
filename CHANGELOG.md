# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-10

### Added

- Task API with create, read, update, delete, and filters for priority and completion.
- Shared error envelope for validation, missing resources, conflicts, and unexpected failures.
- `/health` and `/ready` endpoints, plus a container health check.
- Layered application with a repository port, a SQLite adapter, and an in-memory adapter.
- Unit tests, SQLite integration tests, HTTP tests, and an architecture fitness test.
- Ruff, mypy, pytest, GitHub Actions, Docker, and Make targets.
- Requirements, architecture notes, ADRs, the test strategy, and the release process.
