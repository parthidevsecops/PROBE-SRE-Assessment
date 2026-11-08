"""Single-purpose PROBE SRE workbook ingestion."""
from pathlib import Path
from .assessment_parser import parse_workbook
from .ingest import ingest_assessment
from .graph_builder import PROBEKnowledgeGraph

def ingest_directory(input_dir: Path, chroma_path: str, graph_path: str) -> dict:
    workbook=input_dir/"probe_a.xlsx"
    if not workbook.exists(): raise RuntimeError(f"Required PROBE workbook not found: {workbook}")
    model=parse_workbook(workbook)
    chroma_count=ingest_assessment(model,chroma_path)
    graph=PROBEKnowledgeGraph()
    try:
        graph.clear_database(); graph.add_assessment(model); graph.save(graph_path)
        nodes,edges=graph.node_count,graph.edge_count
    finally: graph.close()
    return {"status":"ready","processed":[{"file":str(workbook),"kg_mode":"probe_structured","sheets":["Q","A","Map","Scoring","Reasoning","Additional"]}],"documents_upserted":chroma_count,"neo4j_nodes":nodes,"neo4j_edges":edges,"principles":model['principles'],"score_summary":[{"name":x['name'],"value":x['value']} for x in model['scores']]}
