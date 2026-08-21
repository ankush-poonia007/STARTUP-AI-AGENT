"""
File        : core/key_rotator.py
Purpose     : Generic API-key rotation utility for provider tools.

Responsibilities:
    - Validate configured API keys.
    - Return keys sequentially through a persistent closure.
    - Raise ToolConnectionError when no keys remain.

This module is provider-agnostic.
It must not import or depend on Groq, Gemini, Tavily, or any provider SDK.
"""

from collections.abc import Callable, Sequence

from src.core.exceptions import ToolConnectionError


def create_key_rotator(keys: Sequence[str]) -> Callable[[], str]:
    """
    Create a stateful callable that returns configured keys sequentially.

    Parameters
    ----------
    keys : Sequence[str]
        API keys available for rotation.

    Returns
    -------
    Callable[[], str]
        Callable returning the next available API key.

    Raises
    ------
    ToolConnectionError
        If no API keys are configured.

    Notes
    -----
    Rotation state is stored inside the returned closure.
    No module-level mutable rotation state is used.
    """
    if not keys:
        raise ToolConnectionError(
            "No API keys configured for key rotation."
        )

    key_list = list(keys)
    current_index = 0

    def get_next_key() -> str:
        nonlocal current_index

        if current_index >= len(key_list):
            raise ToolConnectionError(
                "All configured API keys have been exhausted."
            )

        key = key_list[current_index]
        current_index += 1

        return key

    return get_next_key


if __name__ == "__main__":
    print("Testing key rotation...")
    print("=" * 30)

    mock_keys = ["KEY_1", "KEY_2", "KEY_3"]
    get_next_key = create_key_rotator(mock_keys)

    for expected_key in mock_keys:
        actual_key = get_next_key()
        print(f"Expected: {expected_key} | Got: {actual_key}")
        assert actual_key == expected_key

    print("Rotation test: PASS")

    try:
        get_next_key()
    except ToolConnectionError as error:
        print(f"Exhaustion test: PASS -> {error}")
    else:
        raise AssertionError(
            "Expected ToolConnectionError after all keys were exhausted."
        )

    try:
        create_key_rotator([])
    except ToolConnectionError as error:
        print(f"Empty-key test: PASS -> {error}")
    else:
        raise AssertionError(
            "Expected ToolConnectionError for an empty key list."
        )

    print("=" * 30)
    print("All key rotator tests passed.")
