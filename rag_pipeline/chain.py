"""PROBE SRE assessment Q&A chain.

Retrieval-grounding flow:
    User question
        -> RAG retrieval (ChromaDB + Neo4j)
        -> retrieval grounding check
        -> grounded evidence only
        -> answer LLM
        -> optional answer grounding/correction
        -> final answer
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from .graph_retriever import HybridGraphRetriever
from .principles_engine import extract_principle_context, PRINCIPLES
from .llm_client import chat
from .eval_metrics import evaluate_grounding
from .probe_methodology import PROBE_METHODOLOGY

logger = logging.getLogger(__name__)

INPUT_PATH = os.getenv("INPUT_PATH", "/app/input")
REPORTS_DIR = os.getenv("REPORTS_DIR", "/app/data/reports")

_REPORT_VERB = r"(generate|create|make|build|prepare|export|download|share|send|give\s+me|produce|get\s+me)"
_REPORT_NOUN = r"(report|assessment)"
_REPORT_FORMAT = r"\b(pptx|powerpoint|slide\s?deck|presentation)\b"
_REPORT_KEYWORDS = re.compile(
    rf"{_REPORT_VERB}\W+(?:\w+\W+){{0,3}}{_REPORT_NOUN}|"
    rf"{_REPORT_NOUN}\W+(?:\w+\W+){{0,3}}{_REPORT_VERB}|{_REPORT_FORMAT}",
    re.I,
)


def detect_intent(query):
    return "sre_assessment"


def detect_asis_request(query):
    return False


def detect_narrative_request(query):
    return False


def detect_report_request(query: str) -> bool:
    """True for requests to generate/download the SRE report as a file."""
    return bool(_REPORT_KEYWORDS.search(query or ""))


def _handle_report_request(user_message: str) -> dict:
    from .report_builder import generate_report  # lazy import

    workbook = str(Path(INPUT_PATH) / "probe_a.xlsx")
    logger.info("report_request: q=%r workbook=%s", user_message, workbook)

    try:
        path, llm_used = generate_report(workbook, REPORTS_DIR)
    except Exception as e:
        logger.error("report_request: failed error=%s", e)
        return {
            "text": f"I couldn't generate the report: {e}",
            "mode": "report_error",
            "principles": [],
            "eval_score": 0,
            "evidence_count": 0,
            "vector_evidence_count": 0,
            "graph_evidence_count": 0,
            "report_url": None,
        }

    report_url = f"/reports/{path.name}"
    note = "" if llm_used else " (narrative generated deterministically — the LLM call was unavailable)"
    logger.info("report_request: done url=%s llm_used=%s", report_url, llm_used)

    return {
        "text": f"Your SRE assessment report is ready{note}. Tap the link below to open or download it.",
        "mode": "report",
        "principles": [],
        "eval_score": None,
        "evidence_count": 0,
        "vector_evidence_count": 0,
        "graph_evidence_count": 0,
        "report_url": report_url,
    }


def _build_retrieved_context(r: dict[str, Any], max_items: int = 14) -> str:
    """Build the raw RAG context for grounding and logging."""
    evidence: list[str] = []

    for d in r.get("vector", []):
        evidence.append(f"[VECTOR] {d.get('text', '')}")

    for g in r.get("graph", []):
        evidence.append(
            f"[GRAPH] properties={g.get('properties', {})} "
            f"links={g.get('links', [])}"
        )

    return "\n\n".join(evidence[:max_items])


def _parse_json(raw: str) -> dict[str, Any]:
    """Parse evaluator JSON even if the LLM wraps it in a code fence."""
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


def _ground_retrieved_context(
    question: str,
    raw_context: str,
) -> dict[str, Any]:
    """Check RAG evidence before it is passed to the answer LLM.

    The evaluator is deliberately separate from the answer-generation LLM.
    It decides whether the retrieved evidence is relevant/sufficient and
    returns a smaller grounded_context that the answer LLM is allowed to use.
    """
    if not raw_context.strip():
        return {
            "decision": "FAIL",
            "relevance_score": 0,
            "sufficiency_score": 0,
            "contradiction_found": False,
            "missing_information": ["Relevant PROBE assessment evidence"],
            "relevant_evidence": [],
            "grounded_context": "",
            "explanation": "RAG did not retrieve assessment evidence.",
        }

    evaluator_prompt = f"""
You are the retrieval-grounding gate for the PROBE SRE assessment.

IMPORTANT:
You are evaluating the RAG evidence BEFORE another LLM answers the user.
Do NOT answer the user question.

USER QUESTION:
{question}

RAW RAG EVIDENCE:
{raw_context}

Your job:
1. Identify which retrieved evidence is relevant to the question.
2. Check whether the evidence is sufficient to answer the question.
3. Identify contradictions between retrieved items.
4. Remove irrelevant evidence.
5. Create GROUNDED_CONTEXT containing ONLY evidence that can safely be
   given to the answer-generation LLM.

Rules:
- The assessment evidence is the source of truth for assessment-specific facts.
- Never invent missing facts.
- Never create scores, percentages, dates, findings, or maturity levels.
- If evidence is insufficient, say exactly what is missing.
- Keep useful evidence verbatim or very close to the retrieved text.
- Do not add conclusions that are not explicitly supported.
- If the evidence contains unrelated information, leave it out.

Return ONLY valid JSON:

{{
  "decision": "PASS" or "FAIL",
  "relevance_score": 0,
  "sufficiency_score": 0,
  "contradiction_found": false,
  "missing_information": [],
  "relevant_evidence": [],
  "grounded_context": "",
  "explanation": ""
}}

Decision:
- PASS = enough relevant evidence exists to answer using only that evidence.
- FAIL = evidence is irrelevant, insufficient, or materially contradictory.
"""

    try:
        raw = chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a strict PROBE retrieval-grounding evaluator. "
                        "Return JSON only. Never invent evidence."
                    ),
                },
                {"role": "user", "content": evaluator_prompt},
            ]
        )

        result = _parse_json(raw)

        decision = str(result.get("decision", "FAIL")).upper()
        if decision not in {"PASS", "FAIL"}:
            decision = "FAIL"

        grounded_context = str(result.get("grounded_context", "")).strip()

        # Safety fallback: if the evaluator says PASS but did not return
        # grounded evidence, do not send an empty context to the answer LLM.
        if decision == "PASS" and not grounded_context:
            decision = "FAIL"
            result["explanation"] = (
                "Grounding evaluator returned PASS but no grounded context."
            )

        result["decision"] = decision

        logger.info(
            "retrieval_grounding decision=%s relevance=%s sufficiency=%s "
            "contradiction=%s",
            result.get("decision"),
            result.get("relevance_score"),
            result.get("sufficiency_score"),
            result.get("contradiction_found"),
        )

        return result

    except Exception as exc:
        logger.exception("Retrieval grounding failed: %s", exc)
        return {
            "decision": "FAIL",
            "relevance_score": 0,
            "sufficiency_score": 0,
            "contradiction_found": False,
            "missing_information": ["Unable to validate retrieved evidence"],
            "relevant_evidence": [],
            "grounded_context": "",
            "explanation": f"Retrieval grounding failed: {exc}",
        }


def _build_answer_prompt(
    user_message: str,
    principles: list[str],
    grounded_context: str,
) -> str:
    return f"""You are the PROBE SRE Assessment Assistant.

Answer the user's question using ONLY the GROUNDED ASSESSMENT EVIDENCE below.

The only engineering principles are:
{', '.join(PRINCIPLES)}

Do not invent assessment dimensions that are not present in the evidence.
Do not invent scores, percentages, dates, findings, or maturity levels.
If the grounded evidence is insufficient, say so.
Distinguish workbook-derived findings from general recommendations.

PROBE METHODOLOGY:
{PROBE_METHODOLOGY}

Use the methodology only to interpret terminology and structure the answer.
Never present methodology text as a finding about this assessment.

Relevant principles:
{', '.join(principles)}

GROUNDED ASSESSMENT EVIDENCE:
{grounded_context}

USER QUESTION:
{user_message}
"""


def run_chain(
    user_message,
    history=None,
    excel_path=None,
    chroma_path="./chroma_db",
    graph_path="./graph_db/probe_graph.json",
    stream=False,
):
    if detect_report_request(user_message):
        return _handle_report_request(user_message)

    # ------------------------------------------------------------
    # 1. RETRIEVE
    # ------------------------------------------------------------
    r = HybridGraphRetriever(chroma_path).retrieve(user_message, 8)

    principles = extract_principle_context(user_message)

    vector_n = len(r.get("vector", []))
    graph_n = len(r.get("graph", []))

    raw_context = _build_retrieved_context(r)

    logger.info(
        "query: q=%r vector_docs=%d graph_docs=%d principles=%s",
        user_message,
        vector_n,
        graph_n,
        principles,
    )

    # ------------------------------------------------------------
    # 2. GROUND RAG BEFORE SENDING IT TO THE ANSWER LLM
    # ------------------------------------------------------------
    retrieval_grounding = _ground_retrieved_context(
        user_message,
        raw_context,
    )

    if retrieval_grounding["decision"] != "PASS":
        reason = retrieval_grounding.get(
            "explanation",
            "The retrieved assessment evidence is not sufficient.",
        )

        missing = retrieval_grounding.get("missing_information") or []
        if missing:
            reason += "\nMissing information: " + "; ".join(map(str, missing))

        logger.warning(
            "retrieval_grounding FAIL: q=%r reason=%s",
            user_message,
            reason,
        )

        return {
            "text": (
                "I could not safely answer this question from the retrieved "
                "PROBE assessment evidence.\n\n"
                f"Reason: {reason}"
            ),
            "mode": "sre_assessment",
            "principles": principles,
            "eval_score": 0,
            "grounded": False,
            "evaluation_decision": "ABSTAIN",
            "retrieval_grounding_decision": "FAIL",
            "retrieval_relevance_score": retrieval_grounding.get("relevance_score", 0),
            "retrieval_sufficiency_score": retrieval_grounding.get("sufficiency_score", 0),
            "retrieval_contradiction_found": retrieval_grounding.get(
                "contradiction_found", False
            ),
            "retrieval_missing_information": retrieval_grounding.get(
                "missing_information", []
            ),
            "retrieval_grounding_explanation": reason,
            "evidence_sufficient": False,
            "answer_relevant": False,
            "contradiction_found": False,
            "unsupported_claims": [],
            "missing_evidence": missing,
            "evaluation_explanation": reason,
            "evidence_count": vector_n + graph_n,
            "vector_evidence_count": vector_n,
            "graph_evidence_count": graph_n,
            "report_url": None,
        }

    # IMPORTANT:
    # Only this grounded_context is sent to the answer-generation LLM.
    grounded_context = retrieval_grounding["grounded_context"]

    logger.info(
        "retrieval_grounding PASS: q=%r relevant=%s",
        user_message,
        len(retrieval_grounding.get("relevant_evidence", [])),
    )

    # ------------------------------------------------------------
    # 3. SEND ONLY GROUNDED RAG EVIDENCE TO THE ANSWER LLM
    # ------------------------------------------------------------
    prompt = _build_answer_prompt(
        user_message,
        principles,
        grounded_context,
    )

    answer = chat(
        [
            {
                "role": "system",
                "content": (
                    "You are a grounded SRE assessment analyst. "
                    "Use only the supplied grounded PROBE assessment evidence."
                ),
            },
            {"role": "user", "content": prompt},
        ]
    )

    # ------------------------------------------------------------
    # 4. OPTIONAL SECOND SAFETY CHECK:
    #    Did the answer stay inside the grounded evidence?
    # ------------------------------------------------------------
    evaluation = evaluate_grounding(user_message, answer, r)

    # One bounded correction pass.
    if evaluation.decision == "CORRECT":
        correction_prompt = f"""
Correct the following PROBE SRE assessment answer using ONLY the
GROUNDED ASSESSMENT EVIDENCE.

USER QUESTION:
{user_message}

ORIGINAL ANSWER:
{answer}

GROUNDING EVALUATION:
{evaluation.model_dump_json(indent=2)}

GROUNDED ASSESSMENT EVIDENCE:
{grounded_context}

Rules:
- Remove unsupported claims.
- Correct contradictions.
- Never invent scores, percentages, questions, findings, dates, or reasoning.
- If evidence is insufficient, explicitly say so.
- Separate assessment findings from general recommendations.
- Return only the corrected answer.
"""

        answer = chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a PROBE SRE answer correction agent. "
                        "Stay strictly grounded in supplied evidence."
                    ),
                },
                {"role": "user", "content": correction_prompt},
            ]
        )

        evaluation = evaluate_grounding(user_message, answer, r)

    if evaluation.decision == "ABSTAIN":
        answer = (
            "I could not produce a sufficiently grounded answer from the "
            "available PROBE assessment evidence.\n\n"
            f"Reason: {evaluation.explanation}"
        )

    logger.info(
        "final evaluation: decision=%s score=%.1f grounded=%s",
        evaluation.decision,
        evaluation.grounding_score,
        evaluation.grounded,
    )

    return {
        "text": answer,
        "mode": "sre_assessment",
        "principles": principles,
        "eval_score": evaluation.grounding_score,
        "grounded": evaluation.grounded,
        "evaluation_decision": evaluation.decision,
        "retrieval_grounding_decision": "PASS",
        "retrieval_relevance_score": retrieval_grounding.get("relevance_score", 0),
        "retrieval_sufficiency_score": retrieval_grounding.get("sufficiency_score", 0),
        "retrieval_contradiction_found": retrieval_grounding.get(
            "contradiction_found", False
        ),
        "retrieval_missing_information": retrieval_grounding.get(
            "missing_information", []
        ),
        "retrieval_grounding_explanation": retrieval_grounding.get(
            "explanation", ""
        ),
        "evidence_sufficient": evaluation.evidence_sufficient,
        "answer_relevant": evaluation.answer_relevant,
        "contradiction_found": evaluation.contradiction_found,
        "unsupported_claims": evaluation.unsupported_claims,
        "missing_evidence": evaluation.missing_evidence,
        "evaluation_explanation": evaluation.explanation,
        "evidence_count": vector_n + graph_n,
        "vector_evidence_count": vector_n,
        "graph_evidence_count": graph_n,
        "report_url": None,
    }
