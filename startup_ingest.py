from pathlib import Path
import json, os
from rag_pipeline.generic_ingest import ingest_directory
INPUT_DIR=Path(os.getenv('INPUT_PATH','/app/input')); CHROMA_PATH=os.getenv('CHROMA_PATH','/app/chroma_db'); GRAPH_PATH=os.getenv('GRAPH_PATH','/app/graph_db/probe_graph.json'); STATUS=Path(os.getenv('INGEST_STATUS_FILE','/app/data/ingest_status.json'))
STATUS.parent.mkdir(parents=True,exist_ok=True)
try:
 result=ingest_directory(INPUT_DIR,CHROMA_PATH,GRAPH_PATH); STATUS.write_text(json.dumps(result,indent=2),encoding='utf-8'); print('PROBE SRE ingestion complete:',json.dumps(result,indent=2))
except Exception as e:
 payload={'status':'failed','error':str(e)}; STATUS.write_text(json.dumps(payload,indent=2),encoding='utf-8'); raise
