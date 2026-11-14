# AGENTS.md — Antigravity Multi-Agent Protocol (Argon <-> Hydrogen)

## 1. Role Hierarchy
- **Main Orchestrator & Evaluator (`argon`)**: Runs on Gemini 4 Argon. Responsible for architecture design, specification definition, code review, error root-cause analysis, and final acceptance.
- **Execution Subagent (`hydrogen-executor`)**: Invoked with `Model: "flash"` (or `"flash_lite"`). Responsible for implementing modules, writing scrapers/parsers, generating schemas, and running unit tests inside the sandbox.

## 2. Dual-Config Invariant (Single Source of Truth)
- **Human Source of Truth**: `config/pipeline.human.yaml`
- **Model Protocol Output**: `config/generated/agent_protocol.json`
- **Rule**: Never hand-edit `config/generated/agent_protocol.json` without updating `config/pipeline.human.yaml` and running `python -m backend.core.config_compiler`.

## 3. Handoff & Error Evaluation Protocol
When an execution subagent finishes a task or reports back to `argon`, it must provide a structured summary containing:
1. `files_modified`: List of created/updated file paths.
2. `compile_status`: Output of `python -m backend.core.config_compiler`.
3. `test_status`: Output of `python -m unittest discover -s backend/tests -v`.
4. `open_risks`: Any edge cases or schema ambiguities discovered.

## 4. Domain Constraints
- Maintain unified `Politician` -> `Term` (`LEGISLATOR` | `EXECUTIVE`) extensibility so Phase 1 (Legislative interpellation transcripts & roll-call votes) seamlessly connects to Phase 2 (Mayor/Executive policy promises & execution milestones).
- Every AI-generated summary or policy fulfillment rating in the domain model must preserve verifiable provenance (`source_url`, `session_id`, `start_time_sec`, `end_time_sec`) and Argon audit metadata (`audit_verdict`, `error_code`, `confidence`).
