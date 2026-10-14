"""Static, non-executing inspection of public GitHub source archives."""
import io
import re
import zipfile
from pathlib import PurePosixPath
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

from .models import AnalyzeResponse, Case

MAX_ARCHIVE_BYTES = 12 * 1024 * 1024
MAX_FILES = 800
MAX_FILE_BYTES = 180_000
ALLOWED_EXT = {".tsx", ".jsx", ".ts", ".js", ".vue", ".py", ".java", ".html"}
SKIP_DIRS = {"node_modules", "dist", "build", ".next", "vendor", "coverage", "test", "tests", "__tests__"}


def parse_github_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.port is not None or parsed.username:
        raise HTTPException(400, "Only https://github.com/owner/repo URLs are supported")
    segments = [x for x in parsed.path.strip("/").split("/") if x]
    if len(segments) != 2 or not all(re.fullmatch(r"[A-Za-z0-9_.-]+", x) for x in segments):
        raise HTTPException(400, "Use a GitHub repository root URL")
    owner, repo = segments
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not repo or owner in {".", ".."} or repo in {".", ".."}:
        raise HTTPException(400, "Invalid repository")
    return owner, repo


def route_from_path(path: str) -> str | None:
    p = PurePosixPath(path)
    parts = list(p.parts)
    if "app" in parts and p.name in {"page.tsx", "page.jsx", "page.js", "page.ts"}:
        relative = parts[parts.index("app") + 1:-1]
        relative = [v for v in relative if not (v.startswith("(") and v.endswith(")"))]
        return "/" + "/".join(relative)
    if "pages" in parts and p.suffix in {".tsx", ".jsx", ".ts", ".js"}:
        relative = parts[parts.index("pages") + 1:]
        if relative and relative[0] == "api":
            return None
        relative[-1] = p.stem
        if relative[-1] == "index":
            relative.pop()
        return "/" + "/".join(relative)
    return None


def inspect_files(files: list[tuple[str, str]], repo: str) -> AnalyzeResponse:
    routes: set[str] = set()
    candidates: list[tuple[str, str, str]] = []
    for path, content in files:
        route = route_from_path(path)
        if route:
            routes.add(route)
            candidates.append((route, path, "page"))
        if re.search(r"<form\b|useForm\(|<Form\b", content, re.I):
            candidates.append((route or "/", path, "form"))
        if re.search(r"@(?:Get|Post|Put|Delete|Patch)Mapping\b|@app\.(?:get|post|put|delete)\b|router\.(?:get|post|put|delete)\(", content):
            candidates.append((route or "/", path, "api"))
    cases: list[Case] = []
    for route, path, kind in candidates[:60]:
        title = {"page": "Page loads and main content is visible", "form": "Form validation and submit behavior", "api": "API success and failure responses"}[kind]
        cases.append(Case(id=f"TC{len(cases)+1:03}", title=title, path=route, kind=kind, source=path))
    return AnalyzeResponse(repo=repo, scanned_files=len(files), routes=sorted(routes), cases=cases,
        warnings=["Generated cases are proposals, not verified specifications.",
                  "Dynamic routes, authentication, test data and business assertions require manual configuration."])


async def analyze_public_repo(url: str, branch: str = "") -> AnalyzeResponse:
    owner, repo = parse_github_url(url)
    if branch and not re.fullmatch(r"[A-Za-z0-9_./-]{1,120}", branch):
        raise HTTPException(400, "Invalid branch")
    # Only GitHub API is contacted; no arbitrary user-controlled URL fetch.
    async with httpx.AsyncClient(timeout=25, follow_redirects=False, headers={"Accept": "application/vnd.github+json", "User-Agent": "ai-test-saas-mvp"}) as client:
        info = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
        if info.status_code != 200:
            raise HTTPException(400, "Public repository unavailable or GitHub API limit reached")
        data = info.json()
        if data.get("private") or data.get("size", 0) > 15000:
            raise HTTPException(400, "Repository is private or too large for the MVP")
        ref = branch or data.get("default_branch", "main")
        # GitHub archive endpoint redirects to codeload.github.com. Validate redirect host.
        response = await client.get(f"https://api.github.com/repos/{owner}/{repo}/zipball/{ref}")
        if response.status_code in (301, 302, 307, 308):
            loc = response.headers.get("location", "")
            target = urlparse(loc)
            if target.scheme != "https" or target.hostname != "codeload.github.com":
                raise HTTPException(502, "Unexpected archive redirect")
            response = await client.get(loc)
        if response.status_code != 200:
            raise HTTPException(400, "Cannot download repository archive")
        if len(response.content) > MAX_ARCHIVE_BYTES:
            raise HTTPException(413, "Archive exceeds 12 MB")
    files = []
    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            for entry in archive.infolist():
                path = PurePosixPath(entry.filename)
                if entry.is_dir() or entry.file_size > MAX_FILE_BYTES or entry.compress_size > MAX_FILE_BYTES:
                    continue
                if path.suffix not in ALLOWED_EXT or any(p in SKIP_DIRS for p in path.parts):
                    continue
                if len(files) >= MAX_FILES:
                    break
                with archive.open(entry) as handle:
                    content = handle.read(MAX_FILE_BYTES + 1).decode("utf-8", "replace")
                files.append(("/".join(path.parts[1:]), content))
    except zipfile.BadZipFile as exc:
        raise HTTPException(400, "Invalid repository archive") from exc
    return inspect_files(files, f"{owner}/{repo}")
