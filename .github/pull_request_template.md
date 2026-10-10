## Summary

<!-- What changed and why. Link the issue. -->

## Definition of done

- [ ] Behavior matches the acceptance criteria in `docs/requirements.md`
- [ ] Domain rules live in the domain layer; routes only translate HTTP
- [ ] Errors use the shared envelope (`error`, `message`, `details`)
- [ ] Tests cover the change at the right layer of the pyramid
- [ ] `make check` passes locally (lint, type check, tests)
- [ ] User-facing behavior is described in the README or changelog when it changes
- [ ] No secrets, local databases, or `.env` files are included
- [ ] Logs record events and identifiers, not request bodies

## Reviewer notes

<!-- Risks, migrations, or behavior the reviewer should exercise. -->
