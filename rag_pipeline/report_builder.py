"""Generates the PROBE SRE assessment report as a .pptx.

Design goals (deliberately kept simple / cheap):
  - Exactly ONE LLM call for the whole report's narrative (not one per
    section) — see generate_narrative(). Everything else is deterministic,
    derived straight from parse_workbook()'s already-validated scores.
  - The LLM call is optional: if it fails (no network/token, timeout,
    schema mismatch) the report still generates, using a deterministic
    score-threshold narrative instead. A report should never hard-fail
    just because the LLM is unreachable.
  - All numbers in the deck come from assessment_parser.parse_workbook(),
    the same fixed scoring/reasoning path used by the chat, so the report
    and the chat can never disagree about what a score is.
"""
from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pydantic import BaseModel, Field

from .assessment_parser import parse_workbook
from .probe_methodology import PROBE_METHODOLOGY
from .llm_client import chat_structured

logger = logging.getLogger(__name__)

# Category order the deck follows — matches the Scoring sheet's own column-A
# groupings (see assessment_parser.parse_workbook), which match the
# methodology deck's Foundational / Operational / Outcomes / SRE Dashboard /
# Specialized-scores structure.
CATEGORY_ORDER = ["Foundational", "Operational", "Outcomes and scores", "SRE tech parameters", "Fault and resilience"]

NAVY = RGBColor(0x1B, 0x2A, 0x4A)
ACCENT = RGBColor(0xC9, 0x8A, 0x2E)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
RED = RGBColor(0xC6, 0x28, 0x28)
GREY = RGBColor(0x55, 0x55, 0x55)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


# ---------------------------------------------------------------- context --
def build_report_context(workbook_path: str | Path) -> dict:
    """Group parse_workbook()'s scores by category and attach any matching
    reasoning text, so both the LLM prompt and the deterministic fallback
    work off the same grouped structure."""
    model = parse_workbook(workbook_path)
    reasoning_by_name = {r["name"]: r["text"] for r in model["reasoning"]}
    categories: dict[str, list[dict]] = {c: [] for c in CATEGORY_ORDER}
    for s in model["scores"]:
        base_name = s["name"].split(" — ")[0]  # strip "— Non-prod"/"— Production" suffix for reasoning lookup
        categories.setdefault(s["category"], []).append({
            **s, "reasoning": reasoning_by_name.get(base_name, ""),
        })
    return {"categories": categories, "additional": model["additional"], "principle_scores": model.get("principle_scores", [])}


# ------------------------------------------------------------- narrative --
ProbeCategory = Literal["Foundational", "Operational", "Outcomes and scores", "SRE tech parameters", "Fault and resilience"]


class CategoryNarrative(BaseModel):
    category: ProbeCategory = Field(description="Must be exactly one of the 5 category names as given — NEVER an individual parameter name")
    what_works: list[str] = Field(description="2-5 short bullets, grounded only in the supplied scores/reasoning for this category")
    what_can_improve: list[str] = Field(description="2-5 short bullets, grounded only in the supplied scores/reasoning for this category")


class ActionableArea(BaseModel):
    focus_area: str
    activities: list[str] = Field(description="2-4 short, concrete high-level activities")
    outcome: str = Field(description="One short sentence: what improves if these activities are done")


class ReportNarrative(BaseModel):
    executive_summary: str = Field(description="2-3 sentences, grounded only in the supplied evidence")
    categories: list[CategoryNarrative] = Field(description="Exactly ONE entry per category — Foundational, Operational, Outcomes and scores, SRE tech parameters, Fault and resilience — 5 entries total, never one entry per individual parameter")
    actionable_improvement_areas: list[ActionableArea] = Field(description="3-6 focus areas, prioritising the lowest-scoring evidence")


def _clean_reasoning(text: str, max_len: int = 140) -> str:
    """Workbook reasoning text uses '||' as the source formula's own line
    separator (from an Excel CHAR(10) concatenation) — replace it with a
    readable separator instead of leaking raw '||' into report bullets."""
    if not text: return ""
    cleaned = " · ".join(seg.strip() for seg in text.replace("\n", " ").split("||") if seg.strip())
    return cleaned[:max_len] + ("…" if len(cleaned) > max_len else "")


def _evidence_text(context: dict) -> str:
    lines = []
    for cat in CATEGORY_ORDER:
        rows = context["categories"].get(cat, [])
        if not rows: continue
        lines.append(f"\n[{cat}]")
        for s in rows:
            lines.append(f"- {s['name']}: score {s['value']} ({s['pct_score']}%). Reasoning: {_clean_reasoning(s['reasoning']) or 'n/a'}")
    return "\n".join(lines)


def generate_narrative(context: dict) -> tuple[ReportNarrative, bool]:
    """Returns (narrative, llm_used). Exactly one LLM call is attempted;
    on any failure, falls back to a deterministic narrative so report
    generation never hard-fails on an LLM outage."""
    evidence = _evidence_text(context)
    cats_present = [c for c in CATEGORY_ORDER if context["categories"].get(c)]
    prompt = (
        "You are writing the narrative sections of a PROBE SRE assessment report. "
        "Use ONLY the scores and reasoning given below as facts — never invent a score, "
        "category, or reasoning that isn't supplied. Use the methodology reference only "
        "to choose vocabulary and structure (What Works / What Can Improve / actionable "
        "improvement areas), never as a source of facts about this specific assessment.\n\n"
        f"{PROBE_METHODOLOGY}\nASSESSMENT EVIDENCE:\n{evidence}\n\n"
        f"The evidence above is grouped under exactly {len(cats_present)} bracketed category "
        f"headers: {', '.join(f'[{c}]' for c in cats_present)}. Each line beneath a header is "
        "one SCORED PARAMETER within that category, not a category itself. Produce EXACTLY "
        f"{len(cats_present)} entries in `categories` — one per bracketed header above — never "
        "one entry per parameter line. For each category, write What Works / What Can Improve "
        "bullets summarizing its parameters (higher-scoring items generally belong under What "
        "Works, lower-scoring under What Can Improve — use each parameter's reasoning text to "
        "justify its bullet). Then propose 3-6 actionable improvement areas prioritising the "
        "lowest-scoring parameters across all categories."
    )
    try:
        narrative = chat_structured(
            messages=[
                {"role": "system", "content": "You are a grounded SRE assessment analyst. Every bullet must trace back to the supplied evidence."},
                {"role": "user", "content": prompt},
            ],
            response_model=ReportNarrative,
        )
        got = [c.category for c in narrative.categories]
        if len(got) != len(cats_present) or len(set(got)) != len(got):
            # Model still didn't follow the one-entry-per-category instruction
            # (e.g. duplicated a category, or emitted one per parameter despite
            # the schema constraint). Don't render a broken deck — fall back.
            logger.warning("report narrative: malformed categories=%r (expected %r) — using deterministic fallback", got, cats_present)
            return _fallback_narrative(context), False
        logger.info("report narrative: llm_call=1 model_used=structured categories=%d", len(narrative.categories))
        return narrative, True
    except Exception as e:
        logger.warning("report narrative: LLM call failed (%s) — using deterministic fallback, llm_call=0", e)
        return _fallback_narrative(context), False


def _fallback_narrative(context: dict) -> ReportNarrative:
    """No-LLM narrative: pure score-threshold bucketing using the workbook's
    own reasoning text verbatim. Deliberately plain — this is a safety net,
    not the primary path."""
    categories = []
    all_scored = []
    for cat in CATEGORY_ORDER:
        rows = context["categories"].get(cat, [])
        if not rows: continue
        works, improve = [], []
        for s in rows:
            all_scored.append(s)
            label = f"{s['name']}: {s['pct_score']}%" + (f" — {_clean_reasoning(s['reasoning'], 100)}" if s["reasoning"] else "")
            (works if (s["pct_score"] or 0) >= 60 else improve).append(label)
        categories.append(CategoryNarrative(
            category=cat,
            what_works=works or ["No parameter in this category scored at or above 60%."],
            what_can_improve=improve or ["All parameters in this category scored at or above 60%."],
        ))
    low = sorted(all_scored, key=lambda s: (s["pct_score"] if s["pct_score"] is not None else 999))[:5]
    areas = [ActionableArea(
        focus_area=s["name"],
        activities=[f"Review workbook evidence for {s['name']} ({s['category']})", "Define and track a remediation owner and target date"],
        outcome=f"Improve {s['name']} above its current {s['pct_score']}% score",
    ) for s in low]
    avg = round(sum(s["pct_score"] for s in all_scored if s["pct_score"] is not None) / max(1, len([s for s in all_scored if s["pct_score"] is not None])), 1)
    return ReportNarrative(
        executive_summary=f"This assessment covers {len(all_scored)} scored parameters across {len(categories)} categories, averaging {avg}%. See category sections for detail.",
        categories=categories,
        actionable_improvement_areas=areas,
    )


# ------------------------------------------------------------------ pptx --
def _set_title_slide(prs: Presentation, subtitle: str):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
    title = slide.shapes.add_textbox(Inches(0.8), Inches(2.6), Inches(11.7), Inches(1.4))
    tf = title.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = "PROBE SRE Assessment Report"
    p.font.size = Pt(40); p.font.bold = True; p.font.color.rgb = WHITE
    sub = slide.shapes.add_textbox(Inches(0.8), Inches(3.9), Inches(11.7), Inches(0.6))
    sp = sub.text_frame.paragraphs[0]; sp.text = subtitle
    sp.font.size = Pt(16); sp.font.color.rgb = RGBColor(0xC9, 0xD3, 0xE6)
    return slide


def _add_section_title(slide, text):
    box = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.1), Inches(0.7))
    p = box.text_frame.paragraphs[0]; p.text = text
    p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = NAVY
    return box


def _bulleted_box(slide, left, top, width, height, heading, items, color):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame; tf.word_wrap = True
    hp = tf.paragraphs[0]; hp.text = heading
    hp.font.size = Pt(16); hp.font.bold = True; hp.font.color.rgb = color
    for item in items:
        para = tf.add_paragraph(); para.text = f"•  {item}"
        para.font.size = Pt(12); para.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        para.space_after = Pt(6)


def _score_table_slide(prs: Presentation, title: str, rows: list[dict]):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_section_title(slide, title)
    n = len(rows) + 1
    table_shape = slide.shapes.add_table(n, 3, Inches(0.6), Inches(1.2), Inches(12.1), Inches(0.4 * n))
    table = table_shape.table
    table.columns[0].width = Inches(6.5); table.columns[1].width = Inches(2.8); table.columns[2].width = Inches(2.8)
    for c, h in enumerate(["Parameter", "Score (/7)", "% score"]):
        cell = table.cell(0, c); cell.text = h
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(13)
        cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
        cell.text_frame.paragraphs[0].font.color.rgb = WHITE
    for i, s in enumerate(rows, start=1):
        table.cell(i, 0).text = s["name"]
        table.cell(i, 1).text = "n/a" if s["value"] is None else f"{s['value']:.2f}"
        table.cell(i, 2).text = "n/a" if s["pct_score"] is None else f"{s['pct_score']}%"
        pct_cell = table.cell(i, 2)
        color = GREEN if (s["pct_score"] or 0) >= 60 else (RED if (s["pct_score"] or 0) < 40 else ACCENT)
        for c in range(3):
            table.cell(i, c).text_frame.paragraphs[0].font.size = Pt(12)
        pct_cell.text_frame.paragraphs[0].font.color.rgb = color
        pct_cell.text_frame.paragraphs[0].font.bold = True
    return slide


def render_pptx(context: dict, narrative: ReportNarrative, out_path: str | Path, llm_used: bool) -> Path:
    prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    subtitle = f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} from probe_a.xlsx" + ("" if llm_used else " (narrative: deterministic fallback — LLM unavailable)")
    _set_title_slide(prs, subtitle)

    # Executive summary
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_section_title(slide, "Executive Summary")
    box = slide.shapes.add_textbox(Inches(0.6), Inches(1.4), Inches(12.1), Inches(2.5))
    tf = box.text_frame; tf.word_wrap = True
    tf.paragraphs[0].text = narrative.executive_summary
    tf.paragraphs[0].font.size = Pt(18); tf.paragraphs[0].font.color.rgb = RGBColor(0x22, 0x22, 0x22)

    # Score tables — SRE dashboard and Fault & resilience get their own slide
    # (the ones already validated against Excel's own cached values);
    # Foundational/Operational/Outcomes share the grouped narrative slides below.
    for cat in ["SRE tech parameters", "Fault and resilience"]:
        rows = context["categories"].get(cat, [])
        if rows: _score_table_slide(prs, cat, rows)

    # What Works / What Can Improve, one slide per category — skip the two
    # pure-metric categories (SRE tech parameters, Fault and resilience):
    # they already got a dedicated score table above, have no reasoning
    # text to add, and a narrative slide would just repeat the same four
    # numbers with no new information.
    for cat_narr in narrative.categories:
        if cat_narr.category in ("SRE tech parameters", "Fault and resilience"): continue
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        _add_section_title(slide, f"{cat_narr.category} — What Works / What Can Improve")
        _bulleted_box(slide, Inches(0.6), Inches(1.3), Inches(5.9), Inches(5.6), "What Works", cat_narr.what_works, GREEN)
        _bulleted_box(slide, Inches(6.8), Inches(1.3), Inches(5.9), Inches(5.6), "What Can Improve", cat_narr.what_can_improve, RED)

    # Actionable improvement areas
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_section_title(slide, "Actionable Improvement Areas")
    n = len(narrative.actionable_improvement_areas) + 1
    table_shape = slide.shapes.add_table(n, 3, Inches(0.6), Inches(1.2), Inches(12.1), Inches(0.9 * n))
    table = table_shape.table
    table.columns[0].width = Inches(2.8); table.columns[1].width = Inches(6.0); table.columns[2].width = Inches(3.3)
    for c, h in enumerate(["Focus Area", "High-Level Activities", "What do we achieve"]):
        cell = table.cell(0, c); cell.text = h
        cell.text_frame.paragraphs[0].font.bold = True; cell.text_frame.paragraphs[0].font.size = Pt(13)
        cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
        cell.text_frame.paragraphs[0].font.color.rgb = WHITE
    for i, a in enumerate(narrative.actionable_improvement_areas, start=1):
        table.cell(i, 0).text = a.focus_area
        table.cell(i, 1).text = "\n".join(f"• {x}" for x in a.activities)
        table.cell(i, 2).text = a.outcome
        for c in range(3):
            for para in table.cell(i, c).text_frame.paragraphs:
                para.font.size = Pt(11)

    out_path = Path(out_path); out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out_path)
    return out_path


# --------------------------------------------------------------- orchestrator --
def generate_report(workbook_path: str | Path, out_dir: str | Path) -> tuple[Path, bool]:
    """Full pipeline: parse workbook -> one LLM call (or fallback) -> pptx.
    Returns (file_path, llm_used)."""
    context = build_report_context(workbook_path)
    narrative, llm_used = generate_narrative(context)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = Path(out_dir) / f"probe_sre_report_{stamp}.pptx"
    render_pptx(context, narrative, out_path, llm_used)
    logger.info("report generated: path=%s llm_used=%s", out_path, llm_used)
    return out_path, llm_used
