"""Static PROBE SRE assessment methodology reference.

This is background vocabulary/structure only, taken from the PROBE report
methodology deck (dimensional views, outcomes, SRE dashboard, report
layout). It is NOT customer data and must never be presented as if it were
a finding from probe_a.xlsx. It exists purely so the LLM interprets
workbook terms (e.g. "Automation Maturity", "Service Resilience") using
the same structure the PROBE methodology defines, and can frame summaries
in the same shape (What Works / What Can Improve / Actionable improvement
areas) that PROBE reports use.

Note: this Foundational / Operational / Outcomes lens is a *different*,
more granular grouping of the same Scoring-sheet rows than the five
engineering principles (Reliability, Service Ops, Environment Engineering,
Release Engineering, Security) used elsewhere in this app. Both are valid
views over the same underlying scores; they are not in conflict.
"""

PROBE_METHODOLOGY = """PROBE METHODOLOGY REFERENCE (background structure/vocabulary only — never cite this section itself as a workbook finding; only use it to interpret and frame workbook evidence).

Dimensional views:
- Foundational: covers Architecture, Security and Capacity; SRE decisioning; ITSM structure and chaos management; People skilling and fluidity. Scored via the parameters Service Feedback, SRE Decisioning, Process and Architecture, Automation Maturity, Service Quality, and People Readiness.
- Operational: covers practice maturity split across Non-prod and Production, each assessed on Capacity & flexibility, Process flow, Security & chaos, Tools & leverage, and Alerts & monitoring — tracked separately along the "App and Data" pipeline and the "Pipeline and Infra" pipeline.

Insights:
- Outcomes: Business/Consumer Impact, Service Performance, Service Resilience, and People Toil & Elasticity.
- SRE Dashboard: the four golden signals (Latency, Traffic, Error, Saturation) plus Availability, MTTR (mean time to recovery), MTBF (mean time between failures), and Processing delay.
- Reporting format per assessed service: Business Criticality and Pain Areas, Tech stack, then a "What Works" list and a "What Can Improve" list.
- A summarized outcomes table rolls the Foundational, Operational, and Outcomes parameters into three columns: What Works / What Can Improve / Benefits and Insights.
- An actionable improvement plan breaks remediation into Focus Areas (e.g. Observability, SLI/SLO & error budget, Toil, Production incident, Security test, Chaos Experiments), each with High-Level Activities and the outcome ("What do we achieve").
"""
