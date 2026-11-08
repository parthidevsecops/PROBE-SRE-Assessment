"""FastAPI entrypoint for the PROBE SRE assessment chat.

Serves the DigiCon_UI React app (built by the Docker multi-stage build,
see Dockerfile) as the primary interface, plus the underlying /query and
/health API the SPA (and anything else) talks to. /debug-chat is a
dependency-free fallback page kept for quick verification without relying
on the React build.
"""
from __future__ import annotations
import json, logging, os
from pathlib import Path
from threading import Lock
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rag_pipeline.chain import run_chain

# Configures the root logger so every module's `logging.getLogger(__name__)`
# call (chain.py, llm_client.py, graph_builder.py, ingest.py, ...) actually
# reaches stdout and shows up in `docker compose logs -f probe-app`. Without
# this, logger.info() calls are silently dropped (default root level is
# WARNING with no handler attached).
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

APP_ROOT=Path(__file__).resolve().parent
UI_BUILD=APP_ROOT/'DigiCon_UI'/'build'
INPUT_DIR=Path(os.getenv('INPUT_PATH','/app/input')); CHROMA_PATH=os.getenv('CHROMA_PATH','/app/chroma_db'); GRAPH_PATH=os.getenv('GRAPH_PATH','/app/graph_db/probe_graph.json'); STATUS_FILE=Path(os.getenv('INGEST_STATUS_FILE','/app/data/ingest_status.json'))
REPORTS_DIR=Path(os.getenv('REPORTS_DIR','/app/data/reports')); REPORTS_DIR.mkdir(parents=True,exist_ok=True)
app=FastAPI(title='PROBE SRE Assessment API',version='6.0'); lock=Lock(); history=[]
class QueryRequest(BaseModel): question:str

def status():
 if not STATUS_FILE.exists(): return {'status':'not_ready','error':'ingestion status file missing'}
 try:return json.loads(STATUS_FILE.read_text())
 except Exception as e:return {'status':'not_ready','error':str(e)}

@app.get('/health')
def health():
 s=status(); return {'status':'ok' if s.get('status')=='ready' else 'not_ready','ingestion':s,'neo4j_uri':os.getenv('NEO4J_URI'),'chroma_path':CHROMA_PATH,'ui_build':UI_BUILD.exists()}

@app.get('/debug-chat',response_class=HTMLResponse)
def chat_page():
 return HTMLResponse('''<!doctype html><html><head><meta charset="utf-8"><title>PROBE SRE Assessment (debug)</title><style>body{font-family:Arial,sans-serif;max-width:1000px;margin:30px auto;padding:0 20px;background:#f6f7f9}h1{margin-bottom:4px}.sub{color:#666}.principles span{display:inline-block;padding:7px 10px;border:1px solid #ddd;border-radius:16px;margin:4px;background:white}.box{background:white;border:1px solid #ddd;border-radius:12px;padding:16px;margin-top:18px}.q{width:100%;min-height:100px;padding:12px;box-sizing:border-box;border:1px solid #ccc;border-radius:8px}.btn{margin-top:10px;padding:10px 18px;border:0;border-radius:8px;cursor:pointer}.answer{white-space:pre-wrap;line-height:1.5}.meta{color:#666;font-size:13px}</style></head><body><h1>PROBE SRE Assessment Assistant (debug UI)</h1><div class="sub">Dependency-free fallback; the real UI is served at / once DigiCon_UI is built.</div><div class="principles"><span>Reliability</span><span>Service Ops</span><span>Environment Engineering</span><span>Release Engineering</span><span>Security</span></div><div class="box"><textarea id="q" class="q" placeholder="Ask about the assessment, scores, reasoning, SRE parameters, or additional questions..."></textarea><button class="btn" onclick="ask()">Ask</button></div><div class="box"><div id="meta" class="meta"></div><div id="a" class="answer"></div></div><script>async function ask(){const q=document.getElementById('q').value.trim();if(!q)return;document.getElementById('a').innerHTML='Working...';const r=await fetch('/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});const d=await r.json();if(!r.ok){document.getElementById('a').textContent=JSON.stringify(d,null,2);return;}let html=d.answer.replace(/</g,'&lt;');if(d.report_url){html+='<br><br><a href="'+d.report_url+'" target="_blank" style="display:inline-block;padding:8px 14px;background:#1B2A4A;color:white;border-radius:6px;text-decoration:none;">Download report</a>';}document.getElementById('a').innerHTML=html;document.getElementById('meta').textContent='Principle: '+(d.principles||[]).join(', ')+' | Evidence: '+d.evidence_count+' (vector: '+d.vector_evidence_count+', graph: '+d.graph_evidence_count+') | Groundedness: '+d.eval_score;}</script></body></html>''')

@app.post('/query')
def query(req:QueryRequest):
 q=req.question.strip()
 if not q: raise HTTPException(400,'question is required')
 s=status()
 if s.get('status')!='ready': raise HTTPException(503,detail={'message':'PROBE ingestion is not ready','ingestion':s})
 try:
  with lock:
   result=run_chain(q,history, str(INPUT_DIR/'probe_a.xlsx'),CHROMA_PATH,GRAPH_PATH,False)
   history.extend([{'role':'user','content':q},{'role':'assistant','content':result['text']}])
  logger.info("request: mode=%s vector_docs=%s graph_docs=%s report_url=%s",result['mode'],result.get('vector_evidence_count'),result.get('graph_evidence_count'),result.get('report_url'))
  return {
   'question':q,
   'answer':result['text'],
   'mode':result['mode'],
   'principles':result['principles'],
   'eval_score':result.get('eval_score'),
   'grounded':result.get('grounded'),
   'evaluation_decision':result.get('evaluation_decision'),
   'evidence_sufficient':result.get('evidence_sufficient'),
   'answer_relevant':result.get('answer_relevant'),
   'contradiction_found':result.get('contradiction_found'),
   'unsupported_claims':result.get('unsupported_claims',[]),
   'missing_evidence':result.get('missing_evidence',[]),
   'evaluation_explanation':result.get('evaluation_explanation',''),
   'evidence_count':result['evidence_count'],
   'vector_evidence_count':result['vector_evidence_count'],
   'graph_evidence_count':result['graph_evidence_count'],
   'diagram_path':None,
   'diagram_type':None,
   'report_url':result.get('report_url')
  }
 except Exception as e: raise HTTPException(500,detail=str(e)) from e

@app.get('/report')
def report():
 """Direct, non-chat trigger for report generation — same generator the
 chat path uses when it detects a report request, exposed here for
 scripting/testing without going through /query."""
 from rag_pipeline.report_builder import generate_report
 try:
  path,llm_used=generate_report(str(INPUT_DIR/'probe_a.xlsx'),REPORTS_DIR)
 except Exception as e: raise HTTPException(500,detail=str(e)) from e
 return {'report_url':f'/reports/{path.name}','llm_used':llm_used}

app.mount('/reports',StaticFiles(directory=REPORTS_DIR),name='reports')

# --- React SPA (DigiCon_UI) -------------------------------------------------
# Built by the Dockerfile's node stage into DigiCon_UI/build. Mounted last so
# it never shadows /health, /query, or /debug-chat above. The catch-all
# serves index.html for any path that isn't a real built file, which is what
# lets the SPA's own client-side routing (react-router-dom) work.
if (UI_BUILD/'static').exists():
 app.mount('/static',StaticFiles(directory=UI_BUILD/'static'),name='static')

@app.get('/{full_path:path}')
def react_app(full_path:str):
 requested=UI_BUILD/full_path
 if full_path and requested.is_file(): return FileResponse(requested)
 index_file=UI_BUILD/'index.html'
 if not index_file.exists():
  raise HTTPException(503,'DigiCon UI build is unavailable. Run `docker compose up -d --build` so the Dockerfile\'s node stage builds DigiCon_UI, or visit /debug-chat for a no-build fallback.')
 return FileResponse(index_file)
