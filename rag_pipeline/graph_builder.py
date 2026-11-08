"""PROBE SRE assessment knowledge graph.

The graph is built only from input/probe_a.xlsx. No People/Process/Technology
architecture model is created. The five engineering principles are the only
principle taxonomy used by the application.
"""
from __future__ import annotations
import json, logging, re
from pathlib import Path
from typing import Any
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logger = logging.getLogger(__name__)
DEFAULT_GRAPH_PATH = "./graph_db/probe_graph.json"
PRINCIPLES = ["Reliability", "Service Ops", "Environment Engineering", "Release Engineering", "Security"]


def _id(kind: str, value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")[:100]
    return f"{kind}_{slug or 'unknown'}"


class PROBEKnowledgeGraph:
    def __init__(self) -> None:
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self._nodes = 0
        self._edges = 0

    def close(self) -> None:
        self._driver.close()

    @property
    def node_count(self) -> int:
        with self._driver.session() as s:
            row = s.run("MATCH (n:PROBENode) RETURN count(n) AS c").single()
            return int(row["c"] if row else 0)

    @property
    def edge_count(self) -> int:
        with self._driver.session() as s:
            row = s.run("MATCH (:PROBENode)-[r]->(:PROBENode) RETURN count(r) AS c").single()
            return int(row["c"] if row else 0)

    def clear_database(self) -> None:
        with self._driver.session() as s:
            s.run("MATCH (n) DETACH DELETE n").consume()

    def _node(self, kind: str, label: str, **props: Any) -> str:
        nid = _id(kind, label)
        data = {"id": nid, "node_type": kind, "label": label, **props}
        with self._driver.session() as s:
            s.run("MERGE (n:PROBENode {id:$id}) SET n += $props", id=nid, props=data).consume()
        return nid

    def _edge(self, a: str, b: str, rel: str) -> None:
        rel = re.sub(r"[^A-Z0-9_]", "_", rel.upper()) or "RELATED_TO"
        allowed = {"HAS_PARAMETER","HAS_OPTION","SELECTED","HAS_SCORE","HAS_REASONING","HAS_ADDITIONAL","IN_PRINCIPLE","HAS_CATEGORY","DERIVED_FROM","SUPPORTS"}
        if rel not in allowed: rel = "RELATED_TO"
        with self._driver.session() as s:
            s.run(f"MATCH (a:PROBENode {{id:$a}}),(b:PROBENode {{id:$b}}) MERGE (a)-[:{rel}]->(b)", a=a,b=b).consume()

    def add_assessment(self, model: dict[str, Any]) -> None:
        root = self._node("assessment", "PROBE SRE Assessment", workbook=model.get("workbook", "probe_a.xlsx"))
        for p in PRINCIPLES:
            pid = self._node("principle", p)
            self._edge(root, pid, "IN_PRINCIPLE")
        for item in model.get("questions", []):
            qid = self._node("question", f"Q{item['number']} {item['parameter']}", number=item['number'], category=item.get('category',''), parameter=item['parameter'], selected=item.get('selected',''))
            self._edge(root, qid, "HAS_PARAMETER")
            if item.get("category"):
                cid = self._node("category", item["category"])
                self._edge(qid, cid, "HAS_CATEGORY")
            principle = item.get("principle")
            if principle in PRINCIPLES:
                self._edge(qid, _id("principle", principle), "IN_PRINCIPLE")
            if item.get("selected"):
                aid = self._node("answer", f"Q{item['number']} selected: {item['selected']}", value=item['selected'], question=item['number'])
                self._edge(qid, aid, "SELECTED")
            for opt in item.get("options", []):
                oid = self._node("option", f"Q{item['number']}: {opt.get('text','')}", value=opt.get('text',''), score=opt.get('score'))
                self._edge(qid, oid, "HAS_OPTION")
        for s in model.get("scores", []):
            sid = self._node("score", s["name"], value=s.get("value"), formula=s.get("formula",""), score_category=s.get("category",""))
            self._edge(root, sid, "HAS_SCORE")
        for r in model.get("reasoning", []):
            rid = self._node("reasoning", r["name"], score=r.get("score"), text=r.get("text",""))
            self._edge(root, rid, "HAS_REASONING")
        for a in model.get("additional", []):
            aid = self._node("additional", a["question"], description=a.get("description",""))
            self._edge(root, aid, "HAS_ADDITIONAL")
        for p in model.get("principle_scores", []):
            sid = self._node("principle_score", f"{p['principle']} assessment score", value=p.get('value'), evidence=p.get('evidence',''))
            self._edge(_id("principle", p['principle']), sid, "HAS_SCORE")

    def search(self, text: str, limit: int = 20) -> list[dict[str, Any]]:
        terms = [t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(t) > 2]
        if not terms: return []
        with self._driver.session() as s:
            rows = s.run("""
            MATCH (n:PROBENode)
            WHERE any(t IN $terms WHERE toLower(coalesce(n.label,'')) CONTAINS t OR toLower(coalesce(n.parameter,'')) CONTAINS t OR toLower(coalesce(n.value,'')) CONTAINS t OR toLower(coalesce(n.text,'')) CONTAINS t)
            OPTIONAL MATCH (n)-[r]->(m:PROBENode)
            RETURN n, collect({rel:type(r), target:m.label})[0..5] AS links
            LIMIT $limit
            """, terms=terms, limit=limit)
            return [{"label": row["n"].get("label"), "type": row["n"].get("node_type"), "properties": dict(row["n"]), "links": row["links"]} for row in rows]

    def save(self, path: str) -> None:
        p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        data = {"node_count": self.node_count, "edge_count": self.edge_count, "principles": PRINCIPLES}
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_graph(model: dict[str, Any], graph_path: str = DEFAULT_GRAPH_PATH) -> PROBEKnowledgeGraph:
    g = PROBEKnowledgeGraph()
    g.clear_database(); g.add_assessment(model); g.save(graph_path)
    logger.info("PROBE graph built: %s nodes, %s edges", g.node_count, g.edge_count)
    return g
