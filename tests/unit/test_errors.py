"""Pure error-envelope helpers."""

from fastapi.exceptions import RequestValidationError

from task_api.api.errors import validation_error_details
from task_api.api.schemas import error_body


def test_validation_details_drop_the_body_prefix() -> None:
    exc = RequestValidationError(
        [
            {
                "type": "string_too_short",
                "loc": ("body", "title"),
                "msg": "String should have at least 1 character",
                "input": "",
            },
            {
                "type": "literal_error",
                "loc": ("query", "priority"),
                "msg": "Input should be 'low', 'medium' or 'high'",
                "input": "urgent",
            },
        ]
    )

    assert validation_error_details(exc) == [
        {"field": "title", "message": "String should have at least 1 character"},
        {"field": "priority", "message": "Input should be 'low', 'medium' or 'high'"},
    ]


def test_error_body_always_has_the_same_keys() -> None:
    payload = error_body("not_found", "Task was not found")

    assert payload == {
        "error": "not_found",
        "message": "Task was not found",
        "details": None,
    }
