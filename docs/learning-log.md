# Learning log

Date: 2026-10-10

This log is the guided reading for the reference project. It is written for someone who can already write a Python function and is now practicing how a team specifies, structures, checks, and ships that function.

## What was built

A task API with seven behaviors: create, read, update, delete, filter, validate, and report health. The interesting part is not the task. A task is small enough that every extra file has to justify itself. If a layer does not change the way you test or replace a piece, it is ceremony and it should be deleted.

## How to read the repository

Read in this order. Stop when you can explain the file without looking.

1. `docs/requirements.md`. Notice that each acceptance criterion names a status code or a field. "The update should work" is not a criterion. "An empty patch does not move `updated_at`" is.
2. `src/task_api/domain/models.py`. This file knows what a task is. It does not know HTTP or SQL. That is why `tests/unit/test_domain.py` can construct a `Task` in memory.
3. `src/task_api/application/services.py`. The service is the use case. It loads, asks the model to change, and saves. It does not return a status code.
4. `src/task_api/api/routers/tasks.py`. The route translates. If you find a business rule here, the design has already slipped.
5. `src/task_api/infrastructure/repositories.py`. This is the SQL. Compare it with `infrastructure/memory.py`. Both speak the port in `domain/repositories.py`.
6. `src/task_api/api/dependencies.py` and `main.py`. This is the only place the layers are wired together.
7. `tests/unit/test_architecture.py`. A test that reads imports. It exists because diagrams rot and CI does not.
8. `.github/workflows/ci.yml` and `docs/release-process.md`. The pipeline is the definition of done with a clock on it.

## Practices and the failure they prevent

**User stories and acceptance criteria.** They stop a conversation that ends with "it works on my machine" and no shared example. The criteria are written before the route so the test has something to refuse.

**Definition of ready and definition of done.** Ready is about the story: can someone build it without inventing behavior? Done is about the change: did the checks and the review actually happen? A story can be ready and still not done. Those words are often swapped, and the swap hides unfinished work.

**Layered architecture.** The import rule prevents the domain from importing FastAPI "just this once." The once becomes the way every rule is written, and then the rule can only be tested with a server. ADR 0001 records that we accepted more files in exchange for tests that do not boot one.

**Repository port and two adapters.** The in-memory adapter is not a toy. It returns copies so a service that forgets `save` fails the unit test. The SQLite tests open a second session so a service that only mutated the identity map fails too. Each adapter catches a different cheat.

**Dependency injection.** `Depends` puts the collaborator in the route signature. The readiness test replaces the probe without editing the route. A global session would have forced that test to break the database for the whole process.

**One error envelope.** Clients branch on `error`. If each endpoint invents `{"detail": ...}` or `{"message": ...}`, the client grows a translator per route. The unexpected-error test checks that the exception text, including a fake secret, stays out of the body. Logging the traceback and hiding it from the caller are both required. Doing only one of them is an incident.

**Environment configuration.** `TASK_API_*` and `.env.example` mean a checkout runs without secrets, and a secret never has a reason to be committed. The test fixture deletes those variables so a developer's shell cannot change the suite.

**Test pyramid.** Domain tests are many and small. HTTP tests cover the contract once. Duplicating every domain case through HTTP makes failures slow and vague. The testing strategy says which question belongs at which layer. Use it when you are about to copy a test upward.

**Static analysis in CI.** Ruff and mypy fail the pull request before a reviewer spends time on spacing or a missing `None` check. Review is for behavior. That split only works if the robot actually runs.

**Semantic versioning and Conventional Commits.** The list endpoint returns an array on purpose. Wrapping it later breaks callers, so it is a major change, not a cleanup. The commit type tells a reviewer the intended bump before they read the diff. The changelog still has to be written. Commits are the raw material, not the release notes.

**Rollback.** A tag you can redeploy is a rollback plan. A tag plus a schema change is not, unless you also kept the previous SQLite file. The release checklist forces that sentence to be written before the tag exists. After the incident, nobody wants to invent the sentence.

## Questions worth answering from the code

- Why does `Task` strip the title when the Pydantic model already strips it? What bug appears if you delete one of the two?
- `ping` lives on the repository. What would a second dependency, such as a queue, force you to change?
- The list is a JSON array. Which version bump do you owe a caller if you add `{"tasks": ..., "next": ...}`?
- The architecture test allows `dependencies.py` to import SQLAlchemy. What goes wrong if every route is added to that allowlist "temporarily"?
- `create_all` runs at startup. Why is that safe in this repository and unsafe on a database that already holds someone's tasks?
- The in-memory repository copies tasks on the way in and out. Find the unit test that would still pass if it stored the same object, and name the bug that test would miss.

## What this project will not teach by itself

It will not teach authentication, migrations, or multi-node deploys. Those are omitted on purpose and listed in the requirements. Adding one of them is a good next assignment only if you also update the ADR, the threat to the error model, and the rollback notes. A feature without those three is a demo.
