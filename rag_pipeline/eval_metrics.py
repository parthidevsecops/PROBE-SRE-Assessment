"""Grounding evaluation for PROBE SRE RAG responses.

This module adds an LLM-as-judge gate around the existing RAG response.
It checks whether a generated answer is supported by the retrieved PROBE
assessment evidence and provides structured feedback for one correction pass.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from .llm_client import chat

logger = logging.getLogger(__name__)


class GroundingEvaluation(BaseModel):
    """Structured result from the grounding evaluator."""

    grounded: bool = Field(description="Whether the answer is supported by the evidence.")
    evidence_sufficient: bool = Field(description="Whether enough evidence was retrieved.")
    answer_relevant: bool = Field(description="Whether the answer addresses the question.")
    contradiction_found: bool = Field(description="Whether the answer contradicts evidence.")
    grounding_score: float = Field(ge=0, le=10, description="Grounding score from 0 to 10.")
    unsupported_claims: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    explanation: str = ""
    decision: str = Field(description="PASS, CORRECT, or ABSTAIN.")


def build_evidence_text(context: dict[str, Any]) -> str:
    """Turn retrieved vector and graph records into numbered evidence."""
    lines: list[str] = []
    index = 1

    for item in context.get("vector", []):
        text = item.get("text", "")
        metadata = item.get("metadata", {})
        lines.append(f"[EVIDENCE-{index}] VECTOR | metadata={metadata}\n{text}")
        index += 1

    for item in context.get("graph", []):
        properties = item.get("properties", {})
        links = item.get("links", [])
        lines.append(f"[EVIDENCE-{index}] GRAPH | properties={properties} | links={links}")
        index += 1

    return "\n\n".join(lines)


def _parse_json(raw: str) -> dict[str, Any]:
    """Parse JSON even if the provider wraps it in a markdown code fence."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def evaluate_grounding(
    question: str,
    answer: str,
    context: dict[str, Any],
) -> GroundingEvaluation:
    """Evaluate a generated answer against retrieved PROBE evidence.

    The evaluator treats retrieved assessment evidence as authoritative for
    workbook-specific facts such as questions, answers, scores, findings and
    reasoning. General SRE recommendations are allowed only when labelled as
    recommendations rather than assessment findings.
    """
    evidence = build_evidence_text(context)

    if not evidence.strip():
        return GroundingEvaluation(
            grounded=False,
            evidence_sufficient=False,
            answer_relevant=False,
            contradiction_found=False,
            grounding_score=0,
            unsupported_claims=["No PROBE assessment evidence was retrieved."],
            missing_evidence=["Relevant PROBE assessment evidence"],
            explanation="No assessment evidence was available for validation.",
            decision="ABSTAIN",
        )

    evaluator_prompt = f"""
You are the PROBE SRE Grounding Evaluator.

Do NOT answer the user's question. Evaluate the proposed answer against the
retrieved assessment evidence.

Rules:
1. The supplied PROBE evidence is the only source of truth for workbook-specific facts.
2. Scores, percentages, question numbers, selected answers, reasoning, categories,
   and findings must be supported by the evidence.
3. If a claim cannot be supported, list it as an unsupported claim.
4. If the answer contradicts the evidence, set contradiction_found=true.
5. If the question needs information that is absent, set evidence_sufficient=false.
6. General SRE recommendations may be acceptable only if clearly presented as
   recommendations and not as findings from this assessment.
7. Do not reward professional wording or answer length.

USER QUESTION:
{question}

PROPOSED ANSWER:
{answer}

RETRIEVED PROBE EVIDENCE:
{evidence}

Return ONLY valid JSON:
{{
  "grounded": true,
  "evidence_sufficient": true,
  "answer_relevant": true,
  "contradiction_found": false,
  "grounding_score": 9.0,
  "unsupported_claims": [],
  "missing_evidence": [],
  "explanation": "Short explanation",
  "decision": "PASS"
}}

Decision rules:
- PASS: evidence is sufficient and the answer is grounded.
- CORRECT: evidence exists, but unsupported claims, contradictions, or important
  inaccuracies can be corrected using the current evidence.
- ABSTAIN: the required evidence is missing and the answer cannot safely be corrected.
"""

    try:
        raw = chat([
            {
                "role": "system",
                "content": "You are a strict PROBE RAG grounding evaluator. Return JSON only. Never invent evidence.",
            },
            {"role": "user", "content": evaluator_prompt},
        ])
        result = GroundingEvaluation.model_validate(_parse_json(raw))
        logger.info(
            "grounding_eval decision=%s score=%.1f grounded=%s sufficient=%s contradiction=%s",
            result.decision,
            result.grounding_score,
            result.grounded,
            result.evidence_sufficient,
            result.contradiction_found,
        )
        return result
    except Exception as exc:
        logger.exception("Grounding evaluation failed: %s", exc)
        # Fail closed for assessment-specific responses.
        return GroundingEvaluation(
            grounded=False,
            evidence_sufficient=bool(evidence.strip()),
            answer_relevant=False,
            contradiction_found=False,
            grounding_score=0,
            unsupported_claims=["Grounding evaluator could not validate the response."],
            explanation=f"Evaluation failed: {exc}",
            decision="ABSTAIN",
        )


def score_response(answer: str, context: dict | None = None) -> float:
    """Backward-compatible legacy score for callers that still use it.

    New code should use evaluate_grounding().
    """
    a = (answer or "").strip()
    ctx = context or {}
    evidence = sum(bool(x) for x in [ctx.get("vector"), ctx.get("graph")])
    return round(
        min(
            10.0,
            (5.0 if evidence else 2.0)
            + (3.0 if len(a) > 80 else 1.0)
            + (
                2.0
                if any(k in a.lower() for k in ["score", "assessment", "evidence", "reasoning"])
                else 0.0
            ),
        ),
        1,
    )
