# ADR-0005: Credential and File Source Model

- **Status:** Accepted
- **Date:** 2026-07-09

## Context

Need to define how sinan authenticates to Git repos and how static files enter the system, for v1.

## Decision

### Git repository authentication — out of sinan

v1 targets only repositories **the deploying user can already access** (effectively public repos, or private repos accessible via the server environment's existing git credentials).

- sinan does **not** manage GitHub PATs, Stash tokens, or any Git credentials internally.
- sinan performs a plain `git clone` (HTTPS or SSH). Authentication is handled by the server environment's existing git credential helper / SSH keys / `.netrc`.
- If a clone fails due to auth, sinan surfaces the error clearly; it does not prompt for or store credentials.
- Consequence: no credential storage, no encryption, no per-project secrets. The blast radius of credential leakage is zero from sinan's side.

### Static file sources — three input paths

Static files (Excel, Word, Email, Markdown, Txt) can enter a project via:

1. **Web UI upload** — user uploads a file through the browser. sinan stores it in the project's local file area.
2. **Public URL fetch** — user provides a public HTTP/HTTPS URL. sinan fetches the content server-side. No auth support for URL fetch in v1 (public URLs only).
3. **Local filesystem** — the user places files directly into the project's file structure on the server (a known directory per project). sinan scans and ingests them.

All three converge into the same ingest pipeline once the file bytes are in sinan's hands.

### No credentials stored anywhere in v1

- No PAT/token storage.
- No encryption-at-rest logic for secrets (because there are no secrets).
- File content and the knowledge graph are still stored, but no authentication material is.

## Consequences

- **+** Dramatically simpler v1: no secret management, no encryption key rotation, no credential UI.
- **+** Clear security boundary: sinan never touches credentials. Compromising sinan does not leak Git tokens.
- **−** Cannot access private repos unless the server environment is pre-configured with access. For enterprise Stash deployments this means the ops team must set up git credentials on the server first — an ops prerequisite, not a sinan feature.
- **−** URL fetch is public-only in v1. Authenticated document sources (Confluence, SharePoint) are deferred.
- **Open:** "the server environment's existing git credentials" — need to document this as a deployment prerequisite (ops must configure SSH keys / credential helper on the Linux server before private repos will clone).
