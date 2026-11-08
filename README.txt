PROBE SRE Assessment Processor
==============================

This package is SRE-assessment-only. It processes input/probe_a.xlsx and builds a dedicated PROBE knowledge graph plus ChromaDB vector store.

Engineering principles
----------------------
1. Reliability
2. Service Ops
3. Environment Engineering
4. Release Engineering
5. Security

There is no People/Process/Technology architecture generation and no As-Is/To-Be diagram generation.

Prerequisites
-------------
- Docker Desktop running
- Existing legacy Neo4j container removed
- Docker network: kg-network
- A Hugging Face token with permission to call the configured Inference Provider



1. Create/check network
-----------------------
docker network ls | grep kg-network
If missing:
docker network create kg-network

2. Set the LLM token
--------------------
export HF_TOKEN="YOUR_NEW_TOKEN"
Verify without printing the secret:
echo ${HF_TOKEN:+HF_TOKEN_is_set}

3. Validate compose
-------------------
docker compose config

4. Start PROBE
--------------
docker compose up -d --build

5. Check startup
----------------
docker compose logs -f probe-app

Expected:
- PROBE SRE assessment ingestion
- PROBE graph built with nodes/edges
- PROBE SRE ready. Chat: http://localhost:8501/

The first build also compiles the DigiCon_UI React app (Dockerfile stage
"ui-builder"), which needs network access to npm's registry on your
machine during `docker compose up -d --build`. If that stage fails or you
just want a fast, dependency-free view, use /debug-chat instead.

6. Chat
--------
Open:
http://localhost:8501/         (DigiCon_UI - the full interface)
http://localhost:8501/debug-chat   (plain fallback, no build required)

7. Neo4j
--------
Open:
http://localhost:7474/browser/
Login:
neo4j / password

Useful Cypher:
MATCH (n:PROBENode) RETURN count(n) AS total_nodes;
MATCH (:PROBENode)-[r]->(:PROBENode) RETURN count(r) AS total_relationships;
MATCH (n:PROBENode) RETURN n LIMIT 25;

8. ChromaDB validation
----------------------
docker exec probe-app python -c "import chromadb; c=chromadb.PersistentClient(path='/app/chroma_db'); x=c.get_collection('probe_sre_assessment'); print('count=',x.count())"

9. Health
----------
curl http://localhost:8501/health

10. Query API example
---------------------
curl -s -X POST http://localhost:8501/query -H 'Content-Type: application/json' -d '{"question":"What does the assessment indicate about reliability and observability?"}'


Workbook sources used
---------------------
Q: selected assessment answers
A: answer/score lookup tables
Map: question-to-score mapping
Scoring: assessment score formulas
Reasoning: workbook reasoning definitions
Additional: deeper SRE assessment questions and technical dimensions

The processor does not ingest unrelated repository files into the knowledge base.
