from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    repo_url: str
    branch: str = ""

class Case(BaseModel):
    id: str
    title: str
    path: str
    kind: str
    source: str
    confidence: str = "review_required"

class AnalyzeResponse(BaseModel):
    repo: str
    scanned_files: int
    routes: list[str]
    cases: list[Case]
    warnings: list[str] = Field(default_factory=list)
