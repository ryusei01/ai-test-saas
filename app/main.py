import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from .analyzer import analyze_public_repo
from .models import AnalyzeRequest, AnalyzeResponse

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="AutoTest AI MVP", version="0.1.0")

@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    return await analyze_public_repo(req.repo_url, req.branch)

class ExportRequest(BaseModel):
    cases: list[dict]
    base_url: str = "http://localhost:3000"

@app.post("/api/export")
def export(req: ExportRequest):
    from urllib.parse import urlparse
    import json
    parsed = urlparse(req.base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(400, "Invalid base URL")
    # Data serialized with JSON escaping; do not interpolate user strings as JS code.
    cases = [{"title": str(c.get("title", ""))[:160], "path": str(c.get("path", "/"))[:200],
              "kind": str(c.get("kind", ""))} for c in req.cases[:60] if c.get("kind") == "page"]
    source = '''import { test, expect } from '@playwright/test';

// AI-discovered smoke checks. Add assertions for business behavior before relying on these tests.
const cases = __CASES__;
for (const item of cases) {
  test(`${item.title}: ${item.path}`, async ({ page }) => {
    const target = new URL(item.path, process.env.TEST_BASE_URL || __BASE_URL__);
    await page.goto(target.toString());
    await expect(page.locator('body')).toBeVisible();
    await expect(page.locator('body')).not.toBeEmpty();
  });
}
'''.replace("__CASES__", json.dumps(cases, ensure_ascii=False)).replace("__BASE_URL__", json.dumps(req.base_url))
    return Response(source, media_type="text/plain", headers={"Content-Disposition": 'attachment; filename="generated.spec.ts"'})
