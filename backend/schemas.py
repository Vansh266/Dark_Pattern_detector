from typing import List, Optional
from pydantic import BaseModel


class Rect(BaseModel):
    top: int
    left: int
    width: int
    height: int


class Styles(BaseModel):
    fontSize: str = ""
    color: str = ""
    backgroundColor: str = ""
    opacity: str = "1"


class PageElement(BaseModel):
    id: int
    tag: str
    text: str
    checked: bool = False
    rect: Rect
    styles: Styles


class AnalyzeRequest(BaseModel):
    url: str
    elements: List[PageElement] = []


class Finding(BaseModel):
    element_id: int
    category: str
    method: str
    confidence: Optional[float] = None
    severity: str
    evidence: str
    explanation: str


class TacticSummary(BaseModel):
    category: str
    title: str
    how_it_works: str
    advice: str
    count: int
    worst_severity: str
    points: float
    examples: List[str]


class AnalyzeResponse(BaseModel):
    elements_analyzed: int
    findings: List[Finding]
    counts: dict
    risk_score: int
    risk_band: str
    summary: str
    tactics: List[TacticSummary]

class AnalyzeRequest(BaseModel):
    url: str
    elements: List[PageElement] = []
    mode: str = "hybrid"   # "rules", "ml" or "hybrid" (used for experiments E1-E3 in Step 8)