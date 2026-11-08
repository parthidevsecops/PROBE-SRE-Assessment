"""Five-principle SRE classification only."""
import re
PRINCIPLES=["Reliability","Service Ops","Environment Engineering","Release Engineering","Security"]
KEYWORDS={
"Reliability":["reliability","resilience","slo","sla","sli","latency","availability","error budget","saturation","observability","monitoring","fault","capacity","self healing"],
"Service Ops":["service ops","incident","problem management","change management","support","it service","operations","complaint","pain area"],
"Environment Engineering":["environment","infrastructure","network","provisioning","non-prod","production environment","data integrity"],
"Release Engineering":["release","deployment","pipeline","delivery","rollback","promotion","rollout","cicd"],
"Security":["security","vulnerability","access","identity","compliance","threat","secrets"]}
class PrinciplesEngine:
 def classify(self,text):
  s=text.lower(); scores={p:sum(k in s for k in ks) for p,ks in KEYWORDS.items()}; return sorted([p for p,v in scores.items() if v],key=lambda p:scores[p],reverse=True) or ["Reliability"]
def extract_principle_context(query): return PrinciplesEngine().classify(query)
