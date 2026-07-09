"""
============================================================
BizRadar AI
Document Classifier Benchmark Datasets
============================================================

This package contains all benchmark datasets used for
evaluating the document-routing classifier.

Each module exposes a single list of benchmark cases.

Modules
-------

document_summary

document_qa

document_search

information_extraction

document_comparison

startup_analysis

mvp

tech_stack

coding

general_knowledge

greetings

ambiguous

adversarial

Author
------

BizRadar AI
"""

from .document_summary import DOCUMENT_SUMMARY_CASES
from .document_qa import DOCUMENT_QA_CASES
from .document_search import DOCUMENT_SEARCH_CASES
from .information_extraction import INFORMATION_EXTRACTION_CASES
from .document_comparison import DOCUMENT_COMPARISON_CASES

from .startup_analysis import STARTUP_ANALYSIS_CASES
from .mvp import MVP_CASES
from .tech_stack import TECH_STACK_CASES
from .coding import CODING_CASES
from .general_knowledge import GENERAL_KNOWLEDGE_CASES
from .greetings import GREETING_CASES

from .ambiguous import AMBIGUOUS_CASES
from .adversarial import ADVERSARIAL_CASES

from .startup_documents import STARTUP_DOCUMENT_CASES

__all__ = [

    "DOCUMENT_SUMMARY_CASES",

    "DOCUMENT_QA_CASES",

    "DOCUMENT_SEARCH_CASES",

    "INFORMATION_EXTRACTION_CASES",

    "DOCUMENT_COMPARISON_CASES",

    "STARTUP_ANALYSIS_CASES",

    "MVP_CASES",

    "TECH_STACK_CASES",

    "CODING_CASES",

    "GENERAL_KNOWLEDGE_CASES",

    "GREETING_CASES",

    "AMBIGUOUS_CASES",

    "ADVERSARIAL_CASES",

    "STARTUP_DOCUMENT_CASES",
]