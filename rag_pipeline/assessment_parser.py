"""Parser and deterministic validator for the PROBE SRE workbook."""
from __future__ import annotations
import ast
import operator
import re
from pathlib import Path
from typing import Any
import openpyxl
from .graph_builder import PRINCIPLES

# Safe arithmetic evaluator used for Scoring-sheet formula terms such as
# "(7-Map!G5)*2" or a trailing "*4/6" multiplier, once cell references have
# been substituted with numbers. Only +,-,*,/ and parentheses are permitted.
_SAFE_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _safe_eval(expr: str) -> float:
    node = ast.parse(expr, mode="eval").body

    def _ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _SAFE_OPS:
            return _SAFE_OPS[type(n.op)](_ev(n.left), _ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _SAFE_OPS:
            return _SAFE_OPS[type(n.op)](_ev(n.operand))
        raise ValueError(f"Unsupported expression in scoring formula: {expr!r}")

    return _ev(node)


def _norm(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _colnum(ref: str) -> int:
    n=0
    for c in ref.upper(): n=n*26+ord(c)-64
    return n


def _cell(ws, ref): return ws[ref].value


def _lookup_from_formula(wb, formula: str, data_ws):
    m=re.search(r"VLOOKUP\(Q!([A-Z]+\d+),A!([A-Z]+\d+):([A-Z]+\d+),2,FALSE\)", formula or "", re.I)
    if not m: return None
    qref, start, end=m.groups(); wanted=_norm(_cell(wb["Q"], qref))
    s_col,s_row=re.match(r"([A-Z]+)(\d+)",start).groups(); e_col,e_row=re.match(r"([A-Z]+)(\d+)",end).groups()
    for r in range(int(s_row), int(e_row)+1):
        if _norm(data_ws[f"{s_col}{r}"].value).casefold()==wanted.casefold():
            return data_ws[f"{e_col}{r}"].value
    return None


def map_values(wb):
    q=wb["Q"]; a=wb["A"]; mp=wb["Map"]
    values={}
    for row in mp.iter_rows():
        for cell in row:
            if isinstance(cell.value,str) and cell.value.startswith("="):
                val=_lookup_from_formula(wb,cell.value,a)
                if val is not None: values[cell.coordinate]=float(val) if isinstance(val,(int,float)) else val
    return values


def _q_options(wb, qrow: int, qcol: int):
    q=wb["Q"]; a=wb["A"]; selected=_norm(q.cell(qrow,qcol).value)
    if not selected: return selected, []
    # infer options from adjacent A lookup tables using Map formula on this Q cell
    options=[]
    mp=wb["Map"]
    target=f"{openpyxl.utils.get_column_letter(qcol)}{qrow}"
    for row in mp.iter_rows():
        for c in row:
            f=_norm(c.value)
            if target in f and "VLOOKUP" in f.upper():
                m=re.search(r"A!([A-Z]+)(\d+):([A-Z]+)(\d+)",f)
                if m:
                    sc,sr,ec,er=m.groups()
                    for rr in range(int(sr),int(er)+1):
                        text=_norm(a[f"{sc}{rr}"].value); score=a[f"{ec}{rr}"].value
                        if text: options.append({"text":text,"score":score})
                break
    return selected, options


def _expand_range(start: str, end: str) -> list[str]:
    sc,sr=re.match(r"([A-Z]+)(\d+)",start).groups(); ec,er=re.match(r"([A-Z]+)(\d+)",end).groups()
    return [f"{openpyxl.utils.get_column_letter(c)}{r}"
            for r in range(int(sr),int(er)+1) for c in range(_colnum(sc),_colnum(ec)+1)]


def _split_top_level(body: str) -> list[str]:
    """Split a comma-separated argument list, ignoring commas inside parens."""
    parts=[]; depth=0; cur=""
    for ch in body:
        if ch=="(" : depth+=1
        elif ch==")": depth-=1
        if ch=="," and depth==0:
            parts.append(cur); cur=""
        else:
            cur+=ch
    if cur.strip(): parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def parse_score_formula(formula: str):
    """Backward-compatible helper: flat list of every Map cell referenced
    anywhere in the formula (used by callers/tests that just want the refs,
    not the computed value)."""
    refs=[]
    for token in re.findall(r"Map!([A-Z]+\d+)(?::([A-Z]+\d+))?", formula or "", re.I):
        start,end=token
        refs.extend(_expand_range(start,end) if end else [start])
    return refs


def score_formula(formula: str, mapped: dict[str,Any], scoring_ws):
    """Evaluate a Scoring-sheet formula against `mapped` Map values.

    Handles the two shapes found in the PROBE workbook:
      - plain AVERAGE(Map!X, Map!Y:Z, ...)  -> average of the referenced
        cells, skipping blank/non-numeric cells (matches Excel's AVERAGE,
        which ignores blanks within a range).
      - AVERAGE(<expr>, ...) * <multiplier>, where an <expr> term such as
        "(7-Map!G5)*2" or "Map!D20*2" is an arithmetic expression around one
        or more cell refs. Each such term is evaluated as one arithmetic
        expression (blank/missing refs inside an expression are treated as
        0, matching how Excel treats a blank cell in arithmetic), and the
        outer multiplier (e.g. "*4/6") is applied to the final average.
    """
    formula=(formula or "").strip()
    m=re.match(r"^=\s*AVERAGE\((.*)\)(.*)$", formula, re.I | re.S)
    if not m:
        # Fallback: a bare cell/expression with no AVERAGE wrapper, e.g. "=Map!D4".
        refs=parse_score_formula(formula)
        vals=[mapped[r] for r in refs if isinstance(mapped.get(r),(int,float))]
        return round(sum(vals)/len(vals),4) if vals else None

    body, suffix = m.group(1), m.group(2).strip()
    values: list[float] = []
    for term in _split_top_level(body):
        rm=re.fullmatch(r"Map!([A-Z]+\d+):([A-Z]+\d+)", term, re.I)
        if rm:
            for ref in _expand_range(rm.group(1), rm.group(2)):
                v=mapped.get(ref)
                if isinstance(v,(int,float)): values.append(float(v))
            continue
        rm=re.fullmatch(r"Map!([A-Z]+\d+)", term, re.I)
        if rm:
            v=mapped.get(rm.group(1))
            if isinstance(v,(int,float)): values.append(float(v))
            continue
        # Arithmetic expression term, e.g. "(7-Map!G5)*2" or "Map!D20*2".
        # Substitute each Map!<cell> with its numeric value, treating a
        # blank/missing/non-numeric cell as 0 (Excel arithmetic semantics).
        def _sub(mm):
            v=mapped.get(mm.group(1))
            return repr(float(v)) if isinstance(v,(int,float)) else "0"
        expr=re.sub(r"Map!([A-Z]+\d+)", _sub, term)
        try:
            values.append(_safe_eval(expr))
        except Exception:
            continue

    if not values:
        return None
    avg=sum(values)/len(values)
    if suffix.startswith("*"):
        try:
            avg=_safe_eval(f"({avg}){suffix}")
        except Exception:
            pass
    return round(avg,4)


def infer_principle(category: str, parameter: str) -> str:
    s=f"{category} {parameter}".lower()
    rules=[
      ("Reliability",["reliab","resilien","latency","availability","error","saturation","fault","observability","monitoring","capacity"]),
      ("Service Ops",["incident","problem","change","service operation","support","complaint","pain","it service","operation"]),
      ("Environment Engineering",["environment","infra","infrastructure","non-prod","capacity","network","data integrity"]),
      ("Release Engineering",["release","deployment","pipeline","delivery","prod rollout","change"]),
      ("Security",["security","vulnerability","access","compliance","identity","threat"]),
    ]
    for p,keys in rules:
        if any(k in s for k in keys): return p
    return "Reliability"


def parse_workbook(path: str|Path) -> dict[str,Any]:
    path=Path(path)
    wb=openpyxl.load_workbook(path,data_only=False,read_only=False)
    required={"Q","A","Map","Scoring","Reasoning","Additional"}
    missing=required-set(wb.sheetnames)
    if missing: raise ValueError(f"PROBE workbook missing sheets: {sorted(missing)}")
    # A second, data_only pass gives the last-saved *computed* value for any
    # formula cell (e.g. Reasoning!D, which concatenates the Q selections
    # into readable text). Without this, formula cells surface as raw Excel
    # formula strings instead of the text/number Excel actually shows.
    wb_data=openpyxl.load_workbook(path,data_only=True,read_only=False)
    reasoning_data=wb_data["Reasoning"] if "Reasoning" in wb_data.sheetnames else None

    def _resolved(ws, ws_data, r, c):
        raw=ws.cell(r,c).value
        if isinstance(raw,str) and raw.startswith("=") and ws_data is not None:
            cached=ws_data.cell(r,c).value
            # Only trust the cache if it actually resolved (not a stale #N/A
            # left over from before the workbook's last recalculation).
            if cached is not None and not (isinstance(cached,str) and cached.startswith("#")):
                return cached
        return raw

    q=wb["Q"]; mp=wb["Map"]; scoring=wb["Scoring"]; reasoning=wb["Reasoning"]; add=wb["Additional"]
    mapped=map_values(wb)
    questions=[]
    for r in range(2,q.max_row+1):
        num=q.cell(r,1).value; param=_norm(q.cell(r,3).value)
        if num is None or not param: continue
        cat=_norm(q.cell(r,2).value) or (questions[-1]["category"] if questions else "")
        # columns D onward are selected answers; retain all non-empty selections
        sels=[]
        for c in range(4,q.max_column+1):
            v=_norm(q.cell(r,c).value)
            if v: sels.append(v)
        selected=" | ".join(sels)
        options=[]
        for c in range(4,q.max_column+1):
            s,opts=_q_options(wb,r,c)
            options.extend(opts)
        questions.append({"number":num,"category":cat,"parameter":param,"selected":selected,"options":options,"principle":infer_principle(cat,param)})
    scores=[]; _cat=""
    for r in range(2,scoring.max_row+1):
        name=_norm(scoring.cell(r,2).value)
        raw_cat=_norm(scoring.cell(r,1).value)
        if raw_cat: _cat=raw_cat  # column A is a merged-cell style group header: only set on each group's first row
        if not name: continue
        # Every section uses a single formula in column G, except Operational
        # (rows grouped under "Operational"), which carries two independent
        # formulas: G for the Non-prod rollup, H for the Production rollup
        # (per the row-10 header: C/D = "Non-prod...", E/F = "Prod...").
        # Best-effort label based on that header grouping — worth confirming
        # against the template's original intent if it matters for reporting.
        candidates=[("",scoring.cell(r,7).value)] if _cat!="Operational" else [(" — Non-prod",scoring.cell(r,7).value),(" — Production",scoring.cell(r,8).value)]
        for suffix,formula in candidates:
            formula=_norm(formula)
            if not formula.startswith("="): continue
            value=score_formula(formula,mapped,scoring)
            pct=round(value/7*100,1) if isinstance(value,(int,float)) else None
            scores.append({"name":name+suffix,"category":_cat,"formula":formula,"value":value,"pct_score":pct})
    reasoning_rows=[]
    for r in range(2,reasoning.max_row+1):
        name=_norm(reasoning.cell(r,2).value)
        if name:
            score=next((x.get('value') for x in scores if x['name']==name),None)
            text=_norm(_resolved(reasoning,reasoning_data,r,4))
            reasoning_rows.append({"name":name,"score":score,"text":text})
    additional=[]
    for r in range(2,add.max_row+1):
        qv=_norm(add.cell(r,1).value); desc=_norm(add.cell(r,2).value)
        if qv and qv.lower() not in {"service components: technical architecture points for sre"}:
            additional.append({"question":qv,"description":desc})
    # Derive principle scores from question option scores where possible.
    ps=[]
    for p in PRINCIPLES:
        vals=[]
        for qx in questions:
            if qx['principle']==p:
                chosen={x['text'].casefold():x.get('score') for x in qx['options']}
                for selected in [x.strip() for x in qx['selected'].split('|') if x.strip()]:
                    if isinstance(chosen.get(selected.casefold()),(int,float)): vals.append(float(chosen[selected.casefold()]))
        ps.append({"principle":p,"value":round(sum(vals)/len(vals),4) if vals else None,"evidence":f"Derived from {len(vals)} scored selected responses."})
    return {"workbook":path.name,"principles":PRINCIPLES,"questions":questions,"scores":scores,"reasoning":reasoning_rows,"additional":additional,"principle_scores":ps,"map_values":mapped}
