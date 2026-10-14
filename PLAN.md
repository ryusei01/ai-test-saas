# Product plan

## Goal
Multi-tenant AI-assisted Web test SaaS. Connect a GitHub repository, discover testable features, propose assertions, execute approved tests in the customer's isolated CI environment, and summarize failures.

## Milestones
1. **M0 (implemented):** public repository static inspection, route/form/API candidates, smoke-test export, dashboard, CI and Docker.
2. **M1:** pluggable LLM (Gemini/Ollama), structured JSON output, source-grounded assertions, human review, deterministic fallback and prompt-injection defenses.
3. **M2:** GitHub App OAuth/install flow, private repository access with least privileges, encrypted tokens, multi-user DB and project isolation.
4. **M3:** generate a PR with approved tests, customer-owned GitHub Actions runner, signed callback or scoped token for test results, traces and failure classification.
5. **M4:** subscriptions, quotas (AI tokens and browser-minutes), abuse prevention, billing, retention controls, audit logs, observability.

## Key design decisions
- Never execute untrusted repository code on the SaaS API server.
- Source inspection and expected-value verification are separate. Never mark guessed behavior as verified.
- Avoid sending customer private code to a free LLM tier without explicit informed consent and appropriate data terms.
- Customer-owned CI runners reduce central compute costs but do not remove the need for secure permissions and usage limits.
- Treat source code and repository instructions as untrusted inputs to the LLM.

## Initial data model (future)
users, organizations, memberships, github_installations, projects, scans, discovered_features, test_cases, approvals, test_runs, test_results, artifacts, subscriptions, usage_events.
