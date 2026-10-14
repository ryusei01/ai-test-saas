# AutoTest AI — GitHub-ready MVP

Web app that inspects **public GitHub repositories** without executing their code, discovers Next.js page routes and likely forms/API endpoints, proposes review-required test cases, and exports basic Playwright smoke tests. UI is Japanese.

> **Current scope:** This MVP does **not** yet use an LLM, authenticate with GitHub, run tests remotely, or provide multi-user SaaS billing. Those are explicitly planned in `PLAN.md`. It does not claim generated tests validate business correctness.

## Quick start (Windows PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000. Paste a **public** GitHub repository URL. A default-branch archive is inspected in memory. Optionally specify a branch. Export `generated.spec.ts` and put it in the target project's `tests/` directory.

## Run tests

```bash
pip install -r requirements.txt
pytest -q
```

## Docker

```bash
docker build -t autotest-ai .
docker run --rm -p 8000:8000 autotest-ai
```

## Execute exported Playwright tests in the target repository

1. Install `@playwright/test` in the target app and install Chromium: `npm install -D @playwright/test && npx playwright install chromium`.
2. Copy the downloaded `generated.spec.ts` to `tests/generated.spec.ts` in the **target repository**.
3. Start the target app in another terminal, and run `TEST_BASE_URL=http://localhost:3000 npx playwright test` (PowerShell: `$env:TEST_BASE_URL='http://localhost:3000'; npx playwright test`).
4. `examples/target-workflow.yml` is a **template** for the target repo. Adjust app setup/start commands and dependencies; it is not automatically deployed.

## Safety and limitations

- Only `https://github.com/owner/repo` root URLs accepted; GitHub API + validated codeload redirect. No arbitrary URL fetch.
- Public repositories only; maximum advertised repo size 15 MB, archive 12 MB, 800 selected files, 180 KB per source file.
- Static heuristics are not a full JS/Java/Python parser; routes may be missed and API tests are not generated yet.
- Exported smoke tests only verify a page's body is visible and non-empty. Add specification-based assertions and authentication/test data before production use.
- Do not expose this prototype as a public unlimited endpoint: add rate limiting, authentication, archive streaming limits, and abuse monitoring first.
- `examples/target-workflow.yml` runs target code on GitHub Actions; review workflows and permissions before enabling on untrusted PRs.

## Publish to GitHub

```bash
git init
git add .
git commit -m "Initial AutoTest AI MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-test-saas.git
git push -u origin main
```

Create the empty GitHub repository before `git push`. Never commit `.env` or credentials. License selection is left to the owner; if commercializing, choose a license deliberately.

## Roadmap
See [PLAN.md](PLAN.md).
