"""
============================================================
BizRadar AI
Greetings Benchmark Dataset
============================================================

Purpose
-------
Benchmark queries for evaluating whether the document
classifier correctly avoids routing greetings, small talk,
and casual conversation to document retrieval.

Expected Routing
----------------
False
"""

from typing import Dict, List

CATEGORY = "Greetings"
EXPECTED = False

GREETING = "Greeting"
SMALL_TALK = "Small Talk"
GRATITUDE = "Gratitude"
FAREWELL = "Farewell"
CONVERSATIONAL = "Conversational"


def make_case(case_id: str, intent: str, difficulty: str,
              tags: List[str], query: str) -> Dict:
    return {
        "case_id": case_id,
        "category": CATEGORY,
        "intent": intent,
        "difficulty": difficulty,
        "tags": tags,
        "query": query,
        "expected": EXPECTED,
    }


GREETING_CASES: List[Dict] = [

    # Greetings (GR-001 → GR-004)
    make_case("GR-001", GREETING, "easy",
              ["hello"], "Hello!"),
    make_case("GR-002", GREETING, "easy",
              ["hi"], "Hi there!"),
    make_case("GR-003", GREETING, "easy",
              ["good-morning"], "Good morning."),
    make_case("GR-004", GREETING, "easy",
              ["hey"], "Hey!"),

    # Small Talk (GR-005 → GR-007)
    make_case("GR-005", SMALL_TALK, "easy",
              ["small-talk"], "How are you?"),
    make_case("GR-006", SMALL_TALK, "easy",
              ["small-talk"], "How's your day going?"),
    make_case("GR-007", SMALL_TALK, "medium",
              ["small-talk"], "Nice to meet you."),

    # Gratitude (GR-008 → GR-009)
    make_case("GR-008", GRATITUDE, "easy",
              ["thanks"], "Thank you!"),
    make_case("GR-009", GRATITUDE, "easy",
              ["appreciation"], "I appreciate your help."),

    # Farewell (GR-010)
    make_case("GR-010", FAREWELL, "easy",
              ["bye"], "Goodbye!"),
]
