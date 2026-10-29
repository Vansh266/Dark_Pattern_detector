from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import AnalyzeRequest, AnalyzeResponse
from rules import run_rules
from report import build_report
from merge import merge_findings
from ml.predict import run_ml, model_available
from pricing import run_pricing

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if not model_available():
    print("WARNING: backend/ml/model.joblib not found. Running rules only.")


@app.get("/")
def home():
    return {"message": "Backend is running"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if req.mode in ("rules", "hybrid"):
        rule_findings = run_rules(req.elements) + run_pricing(req.elements)
    else:
        rule_findings = []    
    use_ml = req.mode in ("ml", "hybrid") and model_available()
    ml_findings = run_ml(req.elements) if use_ml else []
    findings = merge_findings(rule_findings, ml_findings)

    counts = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        counts[f.severity] += 1

    risk_score, risk_band, summary, tactics = build_report(findings)

    print(f"{req.url} [{req.mode}]: {len(req.elements)} elements, "
          f"{len(findings)} findings, score {risk_score} ({risk_band})")
    for f in findings:
        print(f"  - [{f.severity}] {f.category} ({f.method}): {f.evidence}")

    return AnalyzeResponse(
        elements_analyzed=len(req.elements),
        findings=findings,
        counts=counts,
        risk_score=risk_score,
        risk_band=risk_band,
        summary=summary,
        tactics=tactics,
    )