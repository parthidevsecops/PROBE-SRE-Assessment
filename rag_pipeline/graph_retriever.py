"""Hybrid PROBE assessment retrieval: Chroma + Neo4j."""
from .ingest import retrieve
from .graph_builder import PROBEKnowledgeGraph

def get_retriever(chroma_path,graph_path=None): return HybridGraphRetriever(chroma_path)
def invalidate_cache(): pass
class HybridGraphRetriever:
 def __init__(self,chroma_path): self.chroma_path=chroma_path
 def retrieve(self,query,limit=8):
  docs=retrieve(query,self.chroma_path,limit)
  g=PROBEKnowledgeGraph()
  try: graph=g.search(query,limit)
  finally:g.close()
  return {"vector":docs,"graph":graph}
