"""
File        : core/key_rotator.py

Purpose     : Generic API-key rotation utility for provider tools.

Responsibilities:
    - Validate configured API keys.
    - Return keys sequentially in a continuous round-robin cycle.
    - Rotate back to the first key after the last key.

This module is provider-agnostic.
It must not import or depend on Groq, Gemini, Tavily, or any provider SDK.
"""

from collections.abc import Callable, Sequence

from src.core.exceptions import ToolConnectionError


def create_key_rotator(keys: Sequence[str]) -> Callable[[], str]:
    """
    Create a stateful callable that returns configured keys
    using continuous round-robin rotation.

    Parameters
    ----------
    keys : Sequence[str]
        API keys available for rotation.

    Returns
    -------
    Callable[[], str]
        Callable returning the next API key.

    Raises
    ------
    ToolConnectionError
        If no API keys are configured.

    Notes
    -----
    Rotation state is stored inside the returned closure.
    No module-level mutable rotation state is used.

    Rotation never exhausts, so callers must enforce their own retry
    limits. Otherwise a provider outage affecting every key would keep
    cycling indefinitely.

    Example
    -------
    Given:

        ["KEY_1", "KEY_2", "KEY_3"]

    Calls return:

        KEY_1 → KEY_2 → KEY_3 → KEY_1 → KEY_2 → ...
    """

    if not keys:
        raise ToolConnectionError(
            "No API keys configured for key rotation."
        )

    key_list = list(keys)
    current_index = 0

    def get_next_key() -> str:
        nonlocal current_index

        key = key_list[current_index]

        current_index = (
            current_index + 1
        ) % len(key_list)

        return key

    return get_next_key


if __name__ == "__main__":

    print("Testing round-robin key rotation...")
    print("=" * 30)

    mock_keys = [
        "KEY_1",
        "KEY_2",
        "KEY_3",
    ]

    get_next_key = create_key_rotator(mock_keys)

    expected_sequence = [
        "KEY_1",
        "KEY_2",
        "KEY_3",
        "KEY_1",
        "KEY_2",
        "KEY_3",
        "KEY_1",
    ]

    for expected_key in expected_sequence:

        actual_key = get_next_key()

        print(
            f"Expected: {expected_key} | "
            f"Got: {actual_key}"
        )

        assert actual_key == expected_key

    print("Round-robin test: PASS")

    try:

        create_key_rotator([])

    except ToolConnectionError as error:

        print(
            f"Empty-key test: PASS -> {error}"
        )

    else:

        raise AssertionError(
            "Expected ToolConnectionError "
            "for an empty key list."
        )

    print("=" * 30)
    print("All key rotator tests passed.")