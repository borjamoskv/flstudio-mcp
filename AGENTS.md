# AGENTS.md — Sovereign Governance & Validation Contract (`flstudio-mcp`)

## 1. Binary Validation Commands (Zero-Exploration Gate)
- **Static Linter (Fail-Closed):** `ruff check . -q`
- **Unit & Protocol Tests:** `pytest -q`

## 2. Repository Invariants
- **Domain:** FastMCP server and BALAG-OMEGA 48 kHz headless audio production bridge for FL Studio.
- **Acoustic Pre-Human Audit Gate (`INV_C5_ACOUSTIC_PRE_HUMAN_AUDIT`):** Every generated `.wav`/`.flac` asset must pass spectral/clipping telemetry verification in silicon before being presented to the operator.

## 3. Exploration Restrictions (`INV_C5_ARGON_GOVERNANCE`)
- Never read binary `.flp`, `.wav`, `.flac`, or `.mp3` files into LLM text context.
- Restrict exploration to Python source modules and MCP tool schema definitions.

## 4. Agent Configuration Governance
- Any PR touching `AGENTS.md`, `.agents/`, or `.claude/` requires explicit human review of its content before merge.
- Do not add project-level hooks or project-level MCP server configuration without human review of each entry.
- Keep permission allowlists strict. Do not use `bypassPermissions` (or equivalent blanket-approval modes) in repositories not under the team's control.
