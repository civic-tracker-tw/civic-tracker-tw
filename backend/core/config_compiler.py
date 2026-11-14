"""
CivicTracker TW - Config Compiler
Compiles human-readable config (pipeline.human.yaml) into machine-oriented
protocol config (agent_protocol.json) with cryptographic hash integrity checking.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

from backend.core.yaml_parser import load_yaml


class ConfigValidationError(Exception):
    """Raised when configuration values fail schema or domain boundary validation."""
    pass


class ConfigDriftError(Exception):
    """Raised when agent_protocol.json source_hash does not match pipeline.human.yaml."""
    pass


def compute_source_hash(file_path: Union[str, Path]) -> str:
    """Computes SHA-256 hash formatted as 'sha256:<hexdigest>'."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {file_path}")
    
    with open(path, "rb") as f:
        content = f.read()
    digest = hashlib.sha256(content).hexdigest()
    return f"sha256:{digest}"


def validate_human_config(cfg: Dict[str, Any]) -> None:
    """
    Validates structural and domain constraints of the human-facing configuration.
    Raises ConfigValidationError if any constraint is violated.
    """
    if not isinstance(cfg, dict):
        raise ConfigValidationError("Top-level config must be a mapping dictionary.")

    # 1. Basic Metadata
    for req_key in ("version", "project_name", "models", "quality_gates", "error_catalog", "data_sources"):
        if req_key not in cfg:
            raise ConfigValidationError(f"Missing required top-level section: '{req_key}'")

    # 2. Models Section
    models = cfg["models"]
    if not isinstance(models, dict):
        raise ConfigValidationError("'models' section must be a dictionary.")
    for role in ("executor", "evaluator"):
        if role not in models:
            raise ConfigValidationError(f"Missing '{role}' definition in 'models' section.")
        m_info = models[role]
        if not isinstance(m_info, dict):
            raise ConfigValidationError(f"'models.{role}' must be a dictionary.")
        for field in ("agent_alias", "provider_model", "temperature"):
            if field not in m_info:
                raise ConfigValidationError(f"Missing '{field}' in models.{role}")
        temp = m_info["temperature"]
        if not (isinstance(temp, (int, float)) and 0.0 <= temp <= 2.0):
            raise ConfigValidationError(f"models.{role}.temperature must be between 0.0 and 2.0, got: {temp}")

    # 3. Quality Gates Section
    gates = cfg["quality_gates"]
    if not isinstance(gates, dict) or len(gates) == 0:
        raise ConfigValidationError("'quality_gates' must be a non-empty dictionary.")

    for gate_name, gate_cfg in gates.items():
        if not isinstance(gate_cfg, dict):
            raise ConfigValidationError(f"Gate '{gate_name}' must be a dictionary.")
        if "task_code" not in gate_cfg or not isinstance(gate_cfg["task_code"], str):
            raise ConfigValidationError(f"Gate '{gate_name}' missing string 'task_code'")

        conf = gate_cfg.get("min_executor_confidence")
        if conf is None or not (isinstance(conf, (int, float)) and 0.0 <= conf <= 1.0):
            raise ConfigValidationError(
                f"Gate '{gate_name}' min_executor_confidence must be in [0.0, 1.0], got: {conf}"
            )

        audit_rate = gate_cfg.get("sample_audit_rate")
        if audit_rate is not None and not (isinstance(audit_rate, (int, float)) and 0.0 <= audit_rate <= 1.0):
            raise ConfigValidationError(
                f"Gate '{gate_name}' sample_audit_rate must be in [0.0, 1.0], got: {audit_rate}"
            )

        # Enums validation
        if "allowed_vote_decisions" in gate_cfg:
            decisions = gate_cfg["allowed_vote_decisions"]
            if not isinstance(decisions, list) or len(decisions) == 0:
                raise ConfigValidationError(f"Gate '{gate_name}' allowed_vote_decisions must be a non-empty list.")
            for d in decisions:
                if not isinstance(d, str) or not d.strip():
                    raise ConfigValidationError(f"Invalid decision enum '{d}' in gate '{gate_name}'")

        if "allowed_fulfillment_statuses" in gate_cfg:
            statuses = gate_cfg["allowed_fulfillment_statuses"]
            if not isinstance(statuses, list) or len(statuses) == 0:
                raise ConfigValidationError(f"Gate '{gate_name}' allowed_fulfillment_statuses must be a non-empty list.")
            for s in statuses:
                if not isinstance(s, str) or not s.strip():
                    raise ConfigValidationError(f"Invalid status enum '{s}' in gate '{gate_name}'")

    # 4. Error Catalog Section
    err_catalog = cfg["error_catalog"]
    if not isinstance(err_catalog, list) or len(err_catalog) == 0:
        raise ConfigValidationError("'error_catalog' must be a non-empty list.")

    valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    seen_codes = set()
    for err in err_catalog:
        if not isinstance(err, dict):
            raise ConfigValidationError("Each entry in 'error_catalog' must be a dictionary.")
        for field in ("code", "severity", "human_label", "model_directive"):
            if field not in err or not isinstance(err[field], str) or not err[field].strip():
                raise ConfigValidationError(f"Error catalog item missing valid '{field}': {err}")
        code = err["code"]
        if code in seen_codes:
            raise ConfigValidationError(f"Duplicate error code in 'error_catalog': {code}")
        seen_codes.add(code)
        if err["severity"] not in valid_severities:
            raise ConfigValidationError(
                f"Invalid severity '{err['severity']}' in error code {code}. Must be one of {valid_severities}"
            )

    # 5. Data Sources Section
    sources = cfg["data_sources"]
    if not isinstance(sources, dict):
        raise ConfigValidationError("'data_sources' must be a dictionary.")
    for phase in ("phase1_legislative", "phase2_executive"):
        if phase not in sources or not isinstance(sources[phase], list):
            raise ConfigValidationError(f"'data_sources' missing list for '{phase}'")
        for src in sources[phase]:
            if not isinstance(src, dict) or "id" not in src or "base_url" not in src:
                raise ConfigValidationError(f"Invalid data source entry in '{phase}': {src}")


def compile_protocol(human_cfg: Dict[str, Any], source_hash: str) -> Dict[str, Any]:
    """
    Transforms the verified human configuration into a compact machine-to-machine protocol
    optimized for token efficiency and strict multi-agent execution.
    """
    validate_human_config(human_cfg)

    models = human_cfg["models"]
    executor = models["executor"]
    evaluator = models["evaluator"]

    routing = {
        "exec_agent": executor["agent_alias"],
        "exec_model": executor["provider_model"],
        "eval_agent": evaluator["agent_alias"],
        "eval_model": evaluator["provider_model"],
        "max_retries": int(executor.get("max_retries_on_reject", 2)),
        "strict_evidence_check": bool(evaluator.get("strict_evidence_check", True)),
    }

    # Compact gates keyed by task_code
    task_gates = {}
    for _, g_data in human_cfg["quality_gates"].items():
        t_code = g_data["task_code"]
        entry = {
            "min_executor_confidence": float(g_data["min_executor_confidence"]),
            "sample_audit_rate": float(g_data.get("sample_audit_rate", 0.0)),
            "always_require_argon_verdict": bool(g_data.get("always_require_argon_verdict", False)),
        }
        if "require_timestamp_bounds" in g_data:
            entry["require_timestamp_bounds"] = bool(g_data["require_timestamp_bounds"])
        if "check_speaker_attribution" in g_data:
            entry["check_speaker_attribution"] = bool(g_data["check_speaker_attribution"])
        if "allowed_vote_decisions" in g_data:
            entry["allowed_vote_decisions"] = list(g_data["allowed_vote_decisions"])
        if "require_verifiable_citation" in g_data:
            entry["require_verifiable_citation"] = bool(g_data["require_verifiable_citation"])
        if "allowed_fulfillment_statuses" in g_data:
            entry["allowed_fulfillment_statuses"] = list(g_data["allowed_fulfillment_statuses"])
        task_gates[t_code] = entry

    # Error directives keyed by code
    err_directives = {}
    for err in human_cfg["error_catalog"]:
        err_directives[err["code"]] = {
            "severity": err["severity"],
            "model_directive": err["model_directive"],
        }

    # Standard Envelope JSON Schemas
    task_code_enums = list(task_gates.keys())
    error_code_enums = list(err_directives.keys())

    wire_schemas = {
        "HydrogenSubmissionEnvelope": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "HydrogenSubmissionEnvelope",
            "type": "object",
            "required": ["task_code", "submission_id", "confidence", "payload", "attempt"],
            "properties": {
                "task_code": {
                    "type": "string",
                    "enum": task_code_enums
                },
                "submission_id": {
                    "type": "string"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "payload": {
                    "type": "object"
                },
                "attempt": {
                    "type": "integer",
                    "minimum": 1
                },
                "previous_error": {
                    "type": ["string", "null"],
                    "enum": error_code_enums + [None]
                }
            }
        },
        "ArgonVerdictEnvelope": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "ArgonVerdictEnvelope",
            "type": "object",
            "required": ["verdict", "task_code", "submission_id", "confidence"],
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": ["APPROVE", "REJECT"]
                },
                "task_code": {
                    "type": "string",
                    "enum": task_code_enums
                },
                "submission_id": {
                    "type": "string"
                },
                "error_code": {
                    "type": ["string", "null"],
                    "enum": error_code_enums + [None]
                },
                "model_directive": {
                    "type": ["string", "null"]
                },
                "evaluator_notes": {
                    "type": ["string", "null"]
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                }
            }
        }
    }

    protocol = {
        "protocol_version": str(human_cfg.get("version", "1.0.0")),
        "project_name": str(human_cfg.get("project_name", "CivicTracker-TW")),
        "evaluation_mode": str(human_cfg.get("evaluation_mode", "QUANTITATIVE_ONLY")),
        "source_hash": source_hash,
        "feature_flags": human_cfg.get("feature_flags", {}),
        "external_endpoints": human_cfg.get("external_endpoints", {}),
        "routing": routing,
        "gates": task_gates,
        "err_directives": err_directives,
        "wire_schemas": wire_schemas,
    }
    return protocol


def verify_source_integrity(human_path: Union[str, Path], protocol_path: Union[str, Path]) -> bool:
    """
    Verifies that the compiled protocol's source_hash matches the current SHA-256 of pipeline.human.yaml.
    Returns True if valid, False if drifted or file missing.
    """
    human = Path(human_path)
    proto = Path(protocol_path)
    if not human.is_file() or not proto.is_file():
        return False

    with open(proto, "r", encoding="utf-8") as f:
        proto_data = json.load(f)

    expected_hash = compute_source_hash(human)
    actual_hash = proto_data.get("source_hash")
    return actual_hash == expected_hash


def compile_config(
    human_config_path: Union[str, Path] = "config/pipeline.human.yaml",
    output_protocol_path: Union[str, Path] = "config/generated/agent_protocol.json",
) -> Dict[str, Any]:
    """
    Main compilation workflow:
    1. Reads and parses pipeline.human.yaml
    2. Calculates SHA-256 source hash
    3. Validates human config schema
    4. Compiles machine protocol
    5. Writes agent_protocol.json atomically
    """
    h_path = Path(human_config_path).resolve()
    o_path = Path(output_protocol_path).resolve()

    if not h_path.is_file():
        raise FileNotFoundError(f"Human configuration file not found at: {h_path}")

    # Compute hash of source file
    src_hash = compute_source_hash(h_path)

    # Load and validate YAML
    cfg_data = load_yaml(str(h_path))
    compiled = compile_protocol(cfg_data, src_hash)

    # Ensure output directory exists
    o_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON protocol
    with open(o_path, "w", encoding="utf-8") as f:
        json.dump(compiled, f, indent=2, ensure_ascii=False)

    return compiled


if __name__ == "__main__":
    base_dir = Path.cwd()
    input_file = base_dir / "config" / "pipeline.human.yaml"
    output_file = base_dir / "config" / "generated" / "agent_protocol.json"

    try:
        result = compile_config(input_file, output_file)
        print(f"[ConfigCompiler] OK: Successfully compiled '{input_file.name}' -> '{output_file.name}'")
        print(f"[ConfigCompiler] Protocol Version: {result['protocol_version']}")
        print(f"[ConfigCompiler] Source Hash: {result['source_hash']}")
        print(f"[ConfigCompiler] Gates: {list(result['gates'].keys())}")
        print(f"[ConfigCompiler] Error Directives: {len(result['err_directives'])} loaded")
        sys.exit(0)
    except Exception as exc:
        print(f"[ConfigCompiler] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
