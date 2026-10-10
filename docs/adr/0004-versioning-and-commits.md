# ADR 0004: Use semantic versioning and Conventional Commits

- Status: Accepted
- Date: 2026-10-10

## Context

The repository is both a running service and a teaching artifact. People will fork it, tag it, and read the history. Without a versioning rule, "0.1" and "the version that fixed delete" become the same conversation. Without a commit rule, the changelog has to be reconstructed from diff reading.

The HTTP list currently returns a JSON array. That fact is part of the versioning decision: the shape is small, and changing it later is visible.

## Decision

Versions follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

- MAJOR changes a contract a caller could already depend on. Examples: removing a field, changing an error code, wrapping the task list in an object, requiring authentication.
- MINOR adds behavior callers can ignore. Examples: a new optional filter, a new read-only field.
- PATCH fixes behavior that disagreed with the documented contract. Examples: a bug where a blank title was stored.

The package version in `pyproject.toml` and `task_api.__version__` is the source of truth. The changelog is updated in the same pull request as the behavior. Git tags use a leading `v`, for example `v0.1.0`. Image tags use the same version without the `v`, plus the commit SHA for the build that produced the image.

Commits follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

```text
<type>: <imperative summary>

- <why this change exists>
```

Types used in this project:

| Type | Use |
| --- | --- |
| `feat` | A minor-level behavior change |
| `fix` | A patch-level correction |
| `docs` | Documentation only |
| `test` | Tests only |
| `refactor` | Behavior-preserving restructure |
| `chore` | Tooling, build, or maintenance |
| `ci` | Pipeline changes |

A breaking change adds `!` after the type or a `BREAKING CHANGE:` footer, and it requires a major bump once the project is past `0.x`. While the version is `0.y.z`, the public contract may still change in a minor bump, and the changelog must say so in plain language. Do not use `0.x` as permission to skip the changelog.

The subject line is imperative and unpunctuated. The body says why. `COMMIT_MESSAGE.md` is the message for the commit that introduces this reference tree.

## Consequences

- Release notes can be drafted from commits, then edited into the changelog. The commits are not a substitute for the changelog.
- A reviewer can see the intended version impact from the type before reading the diff.
- The list endpoint stays an array until a major change. Callers must not depend on undocumented fields.
- Squash merges should keep the conventional subject. A squash title of "updates" destroys the trail this ADR is for.

## Alternatives considered

- Calendar versioning. Clear for an application on a train, and a poor fit for a library-shaped HTTP contract where compatibility is the question students need to practice.
- Unstructured commit messages plus a careful changelog. The changelog still matters. The commit rule makes the changelog possible under time pressure.
