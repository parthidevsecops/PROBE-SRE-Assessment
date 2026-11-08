"""ChromaDB ingestion for the PROBE SRE assessment only."""
from __future__ import annotations
import logging, shutil, re
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)
COLLECTION_NAME = "probe_sre_assessment"
_EF = None


def _get_ef():
    global _EF
    if _EF is None:
        _EF = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-small-en-v1.5"
        )
    return _EF


def _collection(path):
    client = chromadb.PersistentClient(path=path)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_get_ef(),
        metadata={"hnsw:space": "cosine"},
    )


def reset_chroma_store(path="./chroma_db"):
    if Path(path).exists():
        shutil.rmtree(path)


def is_chroma_corruption_error(exc):
    return any(x in str(exc).lower() for x in ["hnsw", "deserializing pickle", "unsupported opcode"])


def _slug(value):
    """Create a stable Chroma-safe identifier component."""
    s = str(value or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "item"


def _unique_id(prefix, value, index):
    """Always produce a unique deterministic ID, even when workbook names repeat."""
    return f"{prefix}_{_slug(value)}_{index}"


def _docs(model):
    docs = []

    def add(doc_id, text, meta):
        docs.append((doc_id, text, meta))

    add(
        "assessment_summary_0",
        f"PROBE SRE assessment workbook: {model['workbook']}. "
        f"Engineering principles: {', '.join(model['principles'])}.",
        {"type": "summary"},
    )

    for idx, q in enumerate(model["questions"], start=1):
        add(
            _unique_id("question", q.get("number"), idx),
            f"Question {q['number']}. Category: {q['category']}. "
            f"Parameter: {q['parameter']}. Selected answer: {q['selected']}. "
            f"Principle: {q['principle']}. Available options and scores: {q['options']}",
            {
                "type": "question",
                "number": str(q["number"]),
                "principle": q["principle"],
            },
        )

    for idx, s in enumerate(model["scores"], start=1):
        add(
            _unique_id("score", s["name"], idx),
            f"Scoring category: {s['name']}. Formula: {s['formula']}. "
            f"Computed score: {s['value']}",
            {"type": "score", "category": s["name"]},
        )

    for idx, r in enumerate(model["reasoning"], start=1):
        # Reasoning contains repeated names in the workbook.  The row index is
        # deliberately part of the ID so every reasoning statement is retained.
        add(
            _unique_id("reasoning", r["name"], idx),
            f"Reasoning category: {r['name']}. Score: {r['score']}. "
            f"Workbook reasoning: {r['text']}",
            {"type": "reasoning", "category": r["name"]},
        )

    for idx, a in enumerate(model["additional"], start=1):
        add(
            _unique_id("additional", a["question"], idx),
            f"Additional SRE assessment question: {a['question']}. "
            f"Description: {a['description']}",
            {"type": "additional"},
        )

    for idx, p in enumerate(model["principle_scores"], start=1):
        add(
            _unique_id("principle", p["principle"], idx),
            f"Engineering principle: {p['principle']}. "
            f"Derived score: {p['value']}. Evidence: {p['evidence']}",
            {"type": "principle", "principle": p["principle"]},
        )

    return docs


def ingest_assessment(model, path):
    c = _collection(path)
    docs = _docs(model)
    if docs:
        ids = [d[0] for d in docs]
        # Defensive validation: fail with a useful message before Chroma does.
        duplicates = sorted({x for x in ids if ids.count(x) > 1})
        if duplicates:
            raise ValueError(f"Internal duplicate Chroma IDs generated: {duplicates}")
        c.upsert(
            ids=ids,
            documents=[d[1] for d in docs],
            metadatas=[d[2] for d in docs],
        )
    return len(docs)


def ingest_documents(docs, path):
    c = _collection(path)
    if docs:
        ids = [d["id"] for d in docs]
        if len(ids) != len(set(ids)):
            raise ValueError("ingest_documents received duplicate IDs")
        c.upsert(
            ids=ids,
            documents=[d["text"] for d in docs],
            metadatas=[d.get("metadata", {}) for d in docs],
        )


def retrieve(query, path, n_results=8):
    c = _collection(path)
    if c.count() == 0:
        return []
    r = c.query(query_texts=[query], n_results=min(n_results, c.count()))
    return [
        {"text": d, "metadata": m, "distance": dist}
        for d, m, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])
    ]
