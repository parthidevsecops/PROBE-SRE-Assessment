"""Rule-based, repeatable evaluation metrics for PROBE RAG.

These checks are deterministic diagnostics. They do not prove semantic truth:
lexical overlap is a measurable signal, not a substitute for an evidence judge.
"""
from __future__ import annotations

import re
from typing import Any

_TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._+-]*")
_STOP_WORDS = {
    "about", "after", "also", "and", "are", "can", "does", "for", "from",
    "how", "into", "is", "it", "its", "may", "not", "of", "on", "or",
    "our", "should", "that", "the", "their", "there", "these", "this",
    "those", "was", "what", "when", "where", "which", "with", "would",
    "you", "your", "in", "to", "a", "an", "be", "as", "by",
}


def _tokens(value: str) -> set[str]:
    return {
        token.lower()
        for token in _TOKEN_RE.findall(value or "")
        if token.lower() not in _STOP_WORDS and len(token) > 2
    }


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def evaluate_retrieval_deterministic(
    question: str,
    raw_context: str,
    grounded_context: str,
    retrieval: dict[str, Any],
) -> dict[str, Any]:
    """Return repeatable retrieval diagnostics; does not make semantic PASS/FAIL."""
    query_terms = _tokens(question)
    raw_terms = _tokens(raw_context)
    grounded_terms = _tokens(grounded_context)
    matched_terms = query_terms & raw_terms
    grounded_matches = query_terms & grounded_terms
    vector_count = len(retrieval.get("vector", []) or [])
    graph_count = len(retrieval.get("graph", []) or [])

    return {
        "evaluation_type": "deterministic",
        "method": "rule_based",
        "checks": {
            "retrieved_evidence_present": bool(raw_context.strip()),
            "grounded_context_present": bool(grounded_context.strip()),
            "vector_documents_present": vector_count > 0,
            "graph_documents_present": graph_count > 0,
        },
        "parameters": {
            "vector_document_count": vector_count,
            "graph_document_count": graph_count,
            "total_document_count": vector_count + graph_count,
            "raw_context_characters": len(raw_context or ""),
            "grounded_context_characters": len(grounded_context or ""),
            "question_keyword_count": len(query_terms),
            "question_keywords_found_in_raw_context": len(matched_terms),
            "question_keywords_found_in_grounded_context": len(grounded_matches),
            "raw_context_keyword_coverage": _ratio(len(matched_terms), len(query_terms)),
            "grounded_context_keyword_coverage": _ratio(len(grounded_matches), len(query_terms)),
        },
        "limitations": [
            "Keyword coverage measures lexical overlap, not semantic relevance or factual correctness.",
            "A deterministic PASS on these checks does not replace the LLM-based semantic grounding decision.",
        ],
    }


def evaluate_answer_deterministic(
    question: str,
    answer: str,
    grounded_context: str,
) -> dict[str, Any]:
    """Return repeatable answer diagnostics; never overrides semantic grounding."""
    question_terms = _tokens(question)
    answer_terms = _tokens(answer)
    evidence_terms = _tokens(grounded_context)
    q_matches = question_terms & answer_terms
    evidence_matches = answer_terms & evidence_terms

    return {
        "evaluation_type": "deterministic",
        "method": "rule_based",
        "checks": {
            "answer_present": bool((answer or "").strip()),
            "answer_has_minimum_content": len((answer or "").split()) >= 8,
        },
        "parameters": {
            "answer_word_count": len((answer or "").split()),
            "question_keyword_count": len(question_terms),
            "question_keywords_found_in_answer": len(q_matches),
            "answer_question_keyword_coverage": _ratio(len(q_matches), len(question_terms)),
            "answer_keyword_count": len(answer_terms),
            "answer_keywords_found_in_grounded_evidence": len(evidence_matches),
            "answer_evidence_keyword_overlap": _ratio(len(evidence_matches), len(answer_terms)),
        },
        "limitations": [
            "Lexical overlap is only a diagnostic signal; valid paraphrases may have low overlap.",
            "This result does not independently identify hallucinations or establish factual support.",
        ],
    }
