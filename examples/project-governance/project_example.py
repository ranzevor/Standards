"""Offline CSV execution and finite project-record checks; Python standard library only."""
from __future__ import annotations

import argparse
import ast
import copy
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import sys
import subprocess
import tempfile

if sys.flags.optimize:
    raise RuntimeError("Run without -O/-OO: the repository validators require normal mode")
if __name__ == '__main__':
    sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from checks import governance_models as g
from checks.finite_schema import schema_check
from checks.candidate_identity import capture_source_identity, verify_source_unchanged

RECORD = ROOT / "examples/project-governance/project-record.json"
SCHEMA = ROOT / "registry/schemas/governance-project.schema.json"
MIN_FREE = 0
PEAK_BYTES = 4 * 1024 * 1024
RESERVE_BYTES = 1024 * 1024
MAX_INPUT_BYTES = 1048576
CONFIG_SCHEMA = {
    "encoding": {"type": "string", "required": True},
    "max_input_bytes": {"type": "integer", "minimum": 1,
                        "maximum": MAX_INPUT_BYTES, "required": True},
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def evaluate_observation(contract: dict, event: dict | None) -> str:
    """Use the shared model's type-sensitive JSON comparison and execution states."""
    return g.evaluate_check(contract, event)


def load_json(path: Path):
    """Use the shared finite parser while preserving the adapter ValueError API."""
    from checks.validation_common import read_json, ValidationError
    try:return read_json(path)
    except ValidationError as error:raise ValueError(str(error)) from error


def local_file(root: Path, relative: str) -> Path:
    p = PurePosixPath(relative)
    g.need(not p.is_absolute() and p.as_posix() == relative
           and ".." not in p.parts and "\\" not in relative, "unsafe project path")
    resolved = (root / p).resolve()
    g.need(resolved.is_relative_to(root.resolve()) and resolved.is_file(),
           "missing or escaping project file: " + relative)
    return resolved


def index_rows(rows: list[dict], label: str) -> dict:
    g.unique([row["id"] for row in rows], label)
    return {row["id"]: row for row in rows}


def validate_adoption_scope(record: dict) -> None:
    selected = g.unique(record["adoption"]["scope_ids"], "adoption scope")
    allowed = g.unique(record["project"]["scope"]["in_scope"], "project scope")
    g.need(selected <= allowed, "adoption scope outside project scope")
    if record["record_state"] == "planned":
        g.need(bool(selected), "planned record needs adoption scope")


def validate_record(record: dict, root: Path = ROOT) -> dict:
    """Check this finite profile, including cross references; never grant authority."""
    root = Path(root).resolve()
    schema_check(record, load_json(root / "registry/schemas/governance-project.schema.json"))
    g.need(g.text(record["id"]) and g.text(record["project"]["id"]), "record/project ID")
    g.need(record["operation_authorized"] is False, "a record is not an operation grant")
    if record["example_only"]:
        g.need(record["project"]["kind"] == "synthetic", "example must be synthetic")
    for decision in [record["adoption"]["decision"]] + [
            x["decision"] for x in record["adoption"]["exceptions"]]:
        if decision["state"] == "not-decided":
            g.need(set(decision) == {"state"}, "undecided cannot invent attribution")
        else:
            g.need(all(g.text(decision.get(k)) for k in ("actor", "at", "reference")),
                   "decision needs actual attribution")
            g.instant(decision["at"])
            g.need(not record["example_only"], "synthetic record cannot claim an actual decision")
    scope = record["project"]["scope"]
    g.need(g.integer(scope["revision"]), "scope revision must be nonnegative")
    inside = g.unique(scope["in_scope"], "in scope")
    outside = g.unique(scope["out_of_scope"], "out of scope")
    g.need(not inside & outside, "scope overlaps explicit exclusions")
    validate_adoption_scope(record)
    if record["record_state"] == "starter":
        g.need(record["project"]["lifecycle"]["state"] == "discovery"
               and not record["checks"]["results"], "starter cannot claim execution")
        return {"schema_consistency": "pass", "readiness": "not-ready",
                "reason": "starter fields are not project acceptance",
                "authority_authenticated": False}

    requirements = index_rows(record["requirements"], "requirements")
    contracts = index_rows(record["acceptance"], "acceptance contracts")
    items = index_rows(record["work_items"], "work items")
    successes = index_rows(record["project"]["success_criteria"], "success criteria")
    index_rows(record["project"]["resources"], "resources")
    index_rows(record["project"]["fixtures"], "fixtures")
    index_rows(record["change"]["findings"], "findings")
    index_rows(record["adoption"]["exceptions"], "exceptions")
    g.need(inside and requirements and contracts and items and successes,
           "planned record lacks required project content")
    required = g.unique(record["checks"]["required_ids"], "required checks")
    g.need(required == set(contracts), "required checks must exactly cover acceptance contracts")
    g.need(g.unique(record["version"]["required_checks"], "release required checks") == required,
           "release required checks differ from project contract")
    for rid, requirement in requirements.items():
        aid = g.unique(requirement["acceptance_ids"], "requirement acceptance")
        wid = g.unique(requirement["work_item_ids"], "requirement work items")
        g.need(requirement["scope_id"] in inside, "requirement outside project scope")
        g.need(requirement["success_criterion_id"] in successes, "missing success criterion")
        g.need(aid and aid <= set(contracts) and wid and wid <= set(items),
               "unresolved requirement trace")
        g.need(all(contracts[x]["requirement_id"] == rid for x in aid),
               "acceptance back-reference mismatch")
        g.need(all(aid <= set(items[x]["acceptance_ids"]) for x in wid),
               "work item lacks requirement acceptance")
        g.need(g.text(requirement["source"]) and g.text(requirement["design"]),
               "requirement source/design missing")
        tree = ast.parse(local_file(root, requirement["implementation_path"]).read_text(encoding="utf-8"))
        g.need(requirement["implementation_symbol"] in {
            n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))},
            "implementation symbol not found")
    for cid, contract in contracts.items():
        rid = contract["requirement_id"]
        g.need(rid in requirements and cid in requirements[rid]["acceptance_ids"],
               "contract missing reverse requirement trace")
        g.need(g.finite_json(contract["expected_value"]), "nonfinite expected outcome")
        g.need(g.integer(contract["expected_exit"]), "expected exit must be a nonnegative integer")
    for sid, success in successes.items():
        ids = g.unique(success["acceptance_ids"], "success acceptance")
        matching = [r for r in requirements.values() if r["success_criterion_id"] == sid]
        g.need(matching and ids == {a for r in matching for a in r["acceptance_ids"]},
               "success/requirement acceptance mismatch")
    for item in items.values():
        g.need(g.integer(item["revision"]), "work revision must be nonnegative")
        g.need(g.unique(item["acceptance_ids"], "work acceptance") <= required and item["acceptance_ids"],
               "work acceptance unresolved")
        g.need(item["state"] == "closed" or item["resolution"] is None,
               "open work item cannot have close resolution")
        if item["state"] == "closed":
            g.need(item["resolution"] is not None, "closed work item needs a resolution")
            if item["resolution"] not in {"verified-fix", "verified-delivery"}:
                g.need(item["history"] and g.text(item["history"][-1].get("reason")),
                       "nonverified closure needs its actual reason")
    closure = g.required_closure(record["work_items"], record["milestone"]["required_ids"])
    g.need(closure == set(items), "milestone omits required project work")
    if record["milestone"]["date_kind"] == "unset":
        g.need("date" not in record["milestone"], "unset date cannot invent a commitment")
    else:
        g.need(g.text(record["milestone"].get("date")), "dated milestone missing date")
    result_rows = record["checks"]["results"]
    result_index = index_rows(result_rows, "check results")
    g.need(set(result_index) <= required, "unknown check result")
    for result in result_rows:
        if result["state"] in {"pass", "fail", "partial", "unknown"}:
            g.need(result["evidence"], "executed check needs evidence")
        elif result["state"] == "not-run":
            g.need(not result["evidence"], "not-run check cannot invent evidence")
    aggregate = g.aggregate_checks(result_rows, record["checks"]["required_ids"])
    for requirement in requirements.values():
        if requirement["state"] == "verified":
            g.need(g.aggregate_checks(result_rows, requirement["acceptance_ids"]) == "pass",
                   "verified requirement lacks passed checks")
    for success in successes.values():
        if success["state"] == "pass":
            g.need(g.aggregate_checks(result_rows, success["acceptance_ids"]) == "pass",
                   "success criterion lacks passed checks")
    for item in items.values():
        if item["state"] == "closed" and item["resolution"] in {"verified-fix", "verified-delivery"}:
            g.need(g.aggregate_checks(result_rows, item["acceptance_ids"]) == "pass",
                   "verified work closure lacks passed checks")
    if record["milestone"]["state"] == "pass" or record["project"]["lifecycle"]["state"] == "accepted":
        g.need(aggregate == "pass" and g.milestone_ready(record["work_items"], list(items)),
               "accepted milestone/project lacks verified necessary work")
    if record["project"]["lifecycle"]["state"] == "accepted":
        g.need(all(x["state"] == "pass" for x in successes.values()),
               "accepted project lacks passed success criteria")
    if record["version"]["preparation_state"] == "ready-for-review":
        g.need(aggregate == "pass", "review-ready candidate lacks necessary current checks")
    g.need(g.integer(record["adoption"]["revision"]), "adoption revision must be nonnegative")
    if record["example_only"]:
        g.need(record["change"]["independent_review"] == "not-run",
               "synthetic record cannot invent independent review")
        g.need(record["adoption"]["state"] == "not-decided",
               "synthetic record cannot claim actual adoption")
    adoption_decision={"not-decided":"not-decided","adopted":"approved","rejected":"rejected","withdrawn":"withdrawn"}
    g.need(record["adoption"]["decision"]["state"] == adoption_decision[record["adoption"]["state"]],
           "adoption state/decision mismatch")
    g.unique(record["change"]["review_units"], "review units")
    for finding in record["change"]["findings"]:
        expected = g.unique(finding["criteria"], "finding criteria")
        closed = g.unique(finding["closed_criteria"], "closed criteria")
        g.need(closed <= expected, "unknown closure criterion")
        if finding["state"] == "closed":
            g.need(expected and closed == expected, "partly closed finding")

    registry = {row["id"]: row for row in load_json(root / "registry/standards.json")}
    seen = set()
    for selection in record["adoption"]["selections"]:
        sid = selection["document_id"]
        g.need(sid in registry and sid not in seen, "unknown/duplicate selected standard")
        seen.add(sid)
        g.need(all(selection[k] == registry[sid][k] for k in ("path", "version", "sha256")),
               "selected standard identity drift")
        body = local_file(root, selection["path"]).read_bytes()
        g.need(digest(body) == selection["sha256"], "selected standard bytes drift")
        from checks.corpus_contract import extract_document
        known = {clause['clause_id'] for clause in extract_document(registry[sid],body.decode('utf-8'))['clauses']}
        clauses = index_rows(selection["clauses"], "selected clauses")
        g.need(set(clauses) <= known, "unknown selected clause")
        if selection["selection"] == "adopted":
            g.need(record["adoption"]["state"] == "adopted"
                   and record["adoption"]["decision"]["state"] == "approved",
                   "adopted selection needs actual decision")
        for clause in clauses.values():
            g.need(set(clause["acceptance_ids"]) <= required, "clause check unresolved")
            if clause["applicability"] == "applicable":
                g.need(clause["acceptance_ids"] or clause["manual_criteria"], "applicable clause lacks check contract")
    g.need(seen, "planned record lacks exact standard selections")
    for exception in record["adoption"]["exceptions"]:
        index_rows(exception["compensations"], "exception compensations")
        g.need(exception["scope"] in inside, "exception outside scope")
        g.need(exception["requirement_id"] in requirements, "exception requirement unresolved")
        g.need(exception["document_sha256"] in {
            row["sha256"] for row in record["adoption"]["selections"]},
            "exception document identity unresolved")
        g.need(g.instant(exception["starts_at"]) < g.instant(exception["expires_at"]),
               "exception has empty validity window")
        if exception["state"] == "approved":
            g.need(exception["decision"]["state"] == "approved", "exception lacks actual decision")
            g.need(record['adoption']['state']=='adopted' and any(
                selection['sha256']==exception['document_sha256'] and selection['selection']=='adopted'
                for selection in record['adoption']['selections']),
                'formal exception requires an adopted project obligation')
    resolved = []
    for row in record["dependencies"]["records"]:
        g.need(row["kind"] == "standard", "this dependency adapter only resolves standards")
        g.need(row["id"] in registry, "dependency standard unresolved")
        selected = registry[row["id"]]
        g.need(row["path"] == selected["path"] and row["expected_sha256"] == selected["sha256"],
               "dependency document identity drift")
        observed = digest(local_file(root, row["path"]).read_bytes())
        resolved.append(dict(row, observed_sha256=observed,
                             resolved_version=registry[row["id"]]["version"]))
    g.validate_dependencies_config(resolved)
    g.need({r["id"] for r in resolved} == seen, "selected standard dependency missing")
    c = record["configuration"]
    config = g.effective_config(c["defaults"], c["environment"], c["command_line"], CONFIG_SCHEMA)
    g.need(config["values"]["encoding"] == "utf-8", "converter only supports explicit utf-8")
    g.need(config["values"]["max_input_bytes"] == record["project"]["io_contract"]["max_input_bytes"],
           "configuration/IO limit mismatch")
    mat = record["materials"]
    g.reclaim_plan(mat["records"], mat["active_ids"], mat["revision"], mat["revision"])
    maintenance = dict(record["maintenance"])
    maintenance.setdefault("actual_owner", None)
    maintenance.setdefault("commitment_reference", None)
    g.validate_maintenance(maintenance)
    if record["deployment"]["applicability"] == "not-applicable":
        g.deployment_safe(record["deployment"])
    from checks.governance_project_profile import validate_proof_scopes
    proof = validate_proof_scopes(record,root)
    if result_rows:
        current_hash = g.canonical_hash(capture_source_identity(root))
        g.need(all(row['candidate_sha256']==current_hash for row in result_rows),
               'check result candidate identity is stale or mixed')
    return {**proof, "schema_consistency": "pass", "record_consistency": "pass",
            "readiness": "contracts-defined", "check_aggregate": aggregate,
            "requirements": len(requirements), "acceptance_contracts": len(contracts),
            "authority_authenticated": False,
            "independent_review_authenticated": False,
            "actual_project_implementation_acceptance": "not-run"}


class ConversionError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def encode_output(raw: bytes, max_input_bytes: int = MAX_INPUT_BYTES) -> bytes:
    """Pure parser/serializer: no file is changed, including on malformed late rows."""
    if not g.integer(max_input_bytes) or not 1 <= max_input_bytes <= MAX_INPUT_BYTES:
        raise ConversionError("input-limit")
    if len(raw) > max_input_bytes:
        raise ConversionError("input-too-large")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ConversionError("encoding") from error
    if "\x00" in text:
        raise ConversionError("nul-character")
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    previous_field_limit = csv.field_size_limit()
    csv.field_size_limit(max(previous_field_limit, max_input_bytes))
    try:
        if next(reader, None) != ["name", "id"]:
            raise ConversionError("header")
        rows = []
        seen = set()
        for row in reader:
            if len(row) != 2:
                raise ConversionError("row-width")
            name, ident = row
            if not name.strip():
                raise ConversionError("empty-name")
            if re.fullmatch(r"[1-9][0-9]*", ident) is None:
                raise ConversionError("id-format")
            if ident in seen:
                raise ConversionError("duplicate-id")
            seen.add(ident)
            rows.append([ident, name])
    except csv.Error as error:
        raise ConversionError("csv-syntax") from error
    finally:
        csv.field_size_limit(previous_field_limit)
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["id", "name"])
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def convert_csv(source: Path, target: Path, expected_input_sha256: str,
                expected_output_sha256: str, *, max_input_bytes: int = MAX_INPUT_BYTES) -> dict:
    """Commit a complete output without replacing any existing path (same filesystem)."""
    source, target = Path(source), Path(target)
    if not g.integer(max_input_bytes) or not 1 <= max_input_bytes <= MAX_INPUT_BYTES:
        raise ConversionError("input-limit")
    if not (g.hash_value(expected_input_sha256) and g.hash_value(expected_output_sha256)):
        raise ConversionError("identity-format")
    if source.resolve() == target.resolve():
        raise ConversionError("same-path")
    if source.is_symlink() or target.is_symlink():
        raise ConversionError("symlink")
    if os.path.lexists(target):
        raise ConversionError("target-exists")
    if not target.parent.is_dir():
        raise ConversionError("target-parent")
    with source.open("rb") as stream:
        raw = stream.read(max_input_bytes + 1)
    if len(raw) > max_input_bytes:
        raise ConversionError("input-too-large")
    if digest(raw) != expected_input_sha256:
        raise ConversionError("input-identity")
    output = encode_output(raw, max_input_bytes)
    if digest(output) != expected_output_sha256:
        raise ConversionError("output-identity")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=".csv-", dir=target.parent,
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(output)
            stream.flush()
            os.fsync(stream.fileno())
        # The example has one writer. This extra observation detects a changed source;
        # it is not a filesystem-wide lock against unrelated concurrent processes.
        if digest(source.read_bytes()) != expected_input_sha256:
            raise ConversionError("input-changed")
        try:
            os.link(temporary, target)  # Atomic no-replace publication on this filesystem.
        except FileExistsError as error:
            raise ConversionError("target-exists") from error
        except OSError as error:
            raise ConversionError("commit-unavailable") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"input_sha256": digest(raw), "output_sha256": digest(target.read_bytes()),
            "input_bytes": len(raw), "output_bytes": len(output)}


def transition_item(item: dict, target: str, expected_revision: int, **kwargs) -> dict:
    """Add explicit record revision history around the existing finite transition API."""
    g.need(g.integer(expected_revision) and expected_revision == item["revision"],
           "stale work revision")
    result = g.transition_work_item(item, target, **kwargs)
    result["revision"] = item["revision"] + 1
    result["history"][-1] = {"from": item["state"], "to": target,
                             "revision": result["revision"]}
    if kwargs.get("reason") is not None:
        result["history"][-1]["reason"] = kwargs["reason"]
    return result


def _csv_observation(scenario: str, record: dict, directory: Path) -> tuple[int | None, dict, dict]:
    fixtures = {f["id"]: f for f in record["project"]["fixtures"]}
    fixture = fixtures[scenario if scenario in fixtures else "normal"]
    source, target = directory / "input.csv", directory / "output.csv"
    raw = fixture["input_text"].encode("utf-8")
    expected = fixture["expected_output_text"].encode("utf-8")
    source.write_bytes(raw)
    input_hash, output_hash = digest(raw), digest(expected)
    if scenario == "wrong-input-identity":
        input_hash = digest(b"different preselected input")
    if scenario == "wrong-output-identity":
        output_hash = digest(b"different preselected output")
    existing = b"existing valid delivery\n"
    if scenario == "existing-output":
        target.write_bytes(existing)
    argv = [sys.executable, "-B", str(Path(__file__).resolve()), "--source", str(source),
            "--target", str(target), "--input-sha256", input_hash,
            "--output-sha256", output_hash, "--max-input-bytes",
            str(record["project"]["io_contract"]["max_input_bytes"])]
    try:
        completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                                   encoding="utf-8", timeout=30, check=False)
    except subprocess.TimeoutExpired as error:
        def captured(value):
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")
        actual = {"execution": "timed-out", "input_unchanged": source.read_bytes() == raw,
                  "output_exists": target.exists()}
        return None, actual, {"argv": argv, "cwd": str(ROOT), "process_exit_code": None,
                              "completion": "timed-out", "stdout": captured(error.stdout),
                              "stderr": captured(error.stderr), "input_sha256": digest(source.read_bytes()),
                              "output_sha256": digest(target.read_bytes()) if target.exists() else None}
    exit_code = completed.returncode
    if exit_code == 0:
        actual = {"output_text": target.read_text(encoding="utf-8"),
                  "input_unchanged": source.read_bytes() == raw}
    else:
        try:
            raw_error = json.loads(completed.stderr)
            error_code = raw_error["error"]
        except (ValueError, KeyError, TypeError):
            error_code = "unexpected-process-failure"
        actual = {"error": error_code, "input_unchanged": source.read_bytes() == raw}
        if scenario == "existing-output":
            actual["existing_unchanged"] = target.read_bytes() == existing
        else:
            actual["output_exists"] = target.exists()
    actual["temporary_files"] = len(list(directory.glob(".csv-*")))
    identities = {"input_sha256": digest(source.read_bytes()), "input_bytes": source.stat().st_size,
                  "expected_input_sha256": input_hash, "expected_output_sha256": output_hash,
                  "output_sha256": digest(target.read_bytes()) if target.exists() else None,
                  "output_bytes": target.stat().st_size if target.exists() else 0,
                  "argv": argv, "cwd": str(ROOT), "process_exit_code": exit_code,
                  "stdout": completed.stdout, "stderr": completed.stderr}
    return exit_code, actual, identities


def _model_observation(scenario: str, record: dict) -> tuple[int, dict]:
    rows = [{"id": "a", "state": "pass"}, {"id": "b", "state": "pass"}]
    if scenario == "missing-check":
        return 0, {"state": g.aggregate_checks(rows[:1], ["a", "b"])}
    if scenario in {"failed-check", "unknown-check"}:
        rows[1]["state"] = "fail" if scenario == "failed-check" else "unknown"
        return 0, {"state": g.aggregate_checks(rows, ["a", "b"])}
    if scenario == "recovery":
        fixture = next(x for x in record["project"]["fixtures"] if x["id"] == "normal")
        raw = fixture["input_text"].encode("utf-8")
        contract = {"id": "recovery-observation", "input_sha256": digest(raw),
                    "environment_sha256": g.canonical_hash({"encoding": "utf-8"}),
                    "layer": "finite-model", "expectation_origin": "requirement",
                    "expected_exit": 0, "expected_value": {"output": fixture["expected_output_text"]}}
        old_event = {k: contract[k] for k in ("id", "input_sha256", "environment_sha256", "layer")}
        old_event.update(completion="timed-out", exit_code=0, actual=None)
        old_state = evaluate_observation(contract, old_event)
        recovered_event = dict(old_event, completion="completed", exit_code=0,
                               actual={"output": encode_output(raw).decode("utf-8")})
        new_state = evaluate_observation(contract, recovered_event)
        g.need(old_event["completion"] == "timed-out", "recovery overwrote original event")
        return 0, {"state": new_state, "original_state": old_state}
    if scenario == "stale-revision":
        current = copy.deepcopy(record["project"]["scope"])
        snapshot = copy.deepcopy(current)
        proposal = {"intent_id": "synthetic-stale-intent", "expected_revision": current["revision"] + 1,
                    "in_scope": list(current["in_scope"]), "out_of_scope": list(current["out_of_scope"]),
                    "decision": {"state": "pending"}}
        try:
            g.apply_scope_change(current, proposal)
        except ValueError as error:
            return 2, {"error": str(error), "unchanged": current == snapshot}
        return 0, {"unexpected_acceptance": True}
    if scenario == "wrong-adoption-scope":
        changed = copy.deepcopy(record)
        changed["adoption"]["scope_ids"] = ["production-deployment"]
        snapshot = copy.deepcopy(changed)
        try:
            validate_adoption_scope(changed)
        except ValueError as error:
            return 2, {"error": str(error), "unchanged": changed == snapshot}
        return 0, {"unexpected_acceptance": True}
    if scenario == "unresolved-dependency":
        try:
            g.required_closure([{"id": "root", "dependencies": ["missing-item"]}], ["root"])
        except ValueError as error:
            return 2, {"error": str(error)}
        return 0, {"unexpected_acceptance": True}
    if scenario == "active-material":
        rows = [{"id": ident, "path": ident + ".bin", "kind": "temporary", "bytes": 1,
                 "sha256": digest(b"x"), "dependencies": ["cache"] if ident == "root" else [],
                 "holds": [], "rebuild_inputs_available": True, "rebuild_command": "synthetic fixture"}
                for ident in ("root", "cache")]
        result = g.reclaim_plan(rows, ["root"], 1, 1)
        byid = {row["id"]: row for row in result["retained"]}
        return 0, {"retained_reason": byid["cache"]["reason"], "files_deleted": result["files_deleted"]}
    from checks.governance_project_profile import observe
    return 0, observe(scenario,record,ROOT)


def run_example(record: dict | None = None) -> dict:
    """Execute predeclared contracts, retain observations, release owned temporary data."""
    started_at = datetime.now(timezone.utc).isoformat()
    record = copy.deepcopy(record if record is not None else load_json(RECORD))
    validation = validate_record(record)
    g.need(record["record_state"] == "planned" and record["example_only"] is True,
           "runner requires the filled synthetic profile")
    g.need(record["project"]["io_contract"]["input_columns"] == ["name", "id"]
           and record["project"]["io_contract"]["output_columns"] == ["id", "name"],
           "runner supports only the declared CSV column profile")
    g.need(sys.version_info >= (3, 12), "Python 3.12 or newer required")
    free_before = shutil.disk_usage(ROOT).free
    g.need(g.capacity_allowed(free_before, PEAK_BYTES, RESERVE_BYTES, MIN_FREE),
           "insufficient workspace capacity for synthetic execution")
    before = capture_source_identity(ROOT)
    for selection in record["adoption"]["selections"]:
        g.need(digest(local_file(ROOT, selection["path"]).read_bytes()) == selection["sha256"],
               "standard changed before execution")
    candidate_hash = g.canonical_hash(before)
    record_hash = g.canonical_hash(record)
    environment = {"python": platform.python_version(), "implementation": platform.python_implementation(),
                   "platform": platform.platform(), "encoding": "utf-8", "columns": ["id", "name"]}
    environment_hash = g.canonical_hash(environment)
    results, observations = [], []
    with tempfile.TemporaryDirectory(prefix="governance-csv-", dir=ROOT.parent) as temp:
        temp_path = Path(temp)
        for item in record["acceptance"]:
            scenario = item["scenario"]
            input_identity = {"scenario": scenario, "fixtures": record["project"]["fixtures"],
                              "candidate_sha256": candidate_hash, "record_canonical_sha256": record_hash}
            contract = {"id": item["id"], "input_sha256": g.canonical_hash(input_identity),
                        "environment_sha256": environment_hash, "layer": item["layer"],
                        "expectation_origin": item["expectation_origin"],
                        "expected_exit": item["expected_exit"], "expected_value": item["expected_value"]}
            identities = {}
            if item["layer"] == "isolated-runtime":
                directory = temp_path / item["id"]
                directory.mkdir()
                exit_code, actual, identities = _csv_observation(scenario, record, directory)
            else:
                exit_code, actual = _model_observation(scenario, record)
            event = {k: contract[k] for k in ("id", "input_sha256", "environment_sha256", "layer")}
            event.update(completion=identities.get("completion", "completed"), exit_code=exit_code, actual=actual)
            state = evaluate_observation(contract, event)
            results.append({"id": item["id"], "state": state, "candidate_sha256": candidate_hash,
                            "evidence": ["observations/" + item["id"]]})
            observations.append({"id": item["id"], "contract": contract, "event": event,
                                 "state": state, "file_identities": identities,
                                 "failure_reason": item["failure_reason"], "recovery": item["recovery"]})
        # Capture the actual temporary set after all handles and conversions have finished.
        materials = [{"id": p.relative_to(temp_path).as_posix(), "path": p.relative_to(temp_path).as_posix(),
                      "kind": "temporary", "bytes": p.stat().st_size, "sha256": digest(p.read_bytes()),
                      "dependencies": [], "holds": [], "rebuild_inputs_available": True,
                      "rebuild_command": "python -B examples/project-governance/project_example.py"}
                     for p in sorted(temp_path.rglob("*")) if p.is_file()]
        active = [m["id"] for m in materials]
        retained = g.reclaim_plan(materials, active, 0, 0)
        g.need(not retained["reclaimable"], "active runtime material cannot be reclaimed")
        # All required evidence bytes, observations and identities now live in the report.
        released = g.reclaim_plan(materials, [], 1, 1)
        g.need(len(released["reclaimable"]) == len(materials), "temporary release plan incomplete")
    aggregate = g.aggregate_checks(results, record["checks"]["required_ids"])
    completed_items = []
    for original in record["work_items"]:
        item = copy.deepcopy(original)
        for target in ("triaged", "in-progress", "verification"):
            item = transition_item(item, target, item["revision"])
        evidence = {r["id"]: r["state"] for r in results if r["id"] in item["acceptance_ids"]}
        if set(evidence) == set(item["acceptance_ids"]) and all(x == "pass" for x in evidence.values()):
            item = transition_item(item, "closed", item["revision"],
                                   resolution="verified-delivery", evidence=evidence)
        completed_items.append(item)
    after = verify_source_unchanged(ROOT, before)
    return {"record_id": record["id"], "validation": validation,
            "started_at": started_at, "finished_at": datetime.now(timezone.utc).isoformat(),
            "command": [sys.executable, "-B", "examples/project-governance/project_example.py"],
            "cwd": str(ROOT),
            "tool_versions": environment, "candidate_sha256": candidate_hash,
            "record_canonical_sha256": record_hash,
            "source_identity": before, "source_unchanged": before == after,
            "observations": observations, "checks": results, "aggregate": aggregate,
            "requirement_results": [{"id": row["id"], "acceptance_ids": row["acceptance_ids"],
                                     "state": g.aggregate_checks(results, row["acceptance_ids"])}
                                    for row in record["requirements"]],
            "success_results": [{"id": row["id"], "acceptance_ids": row["acceptance_ids"],
                                 "state": g.aggregate_checks(results, row["acceptance_ids"])}
                                for row in record["project"]["success_criteria"]],
            "work_items": completed_items,
            "milestone_ready_in_model": g.milestone_ready(completed_items, record["milestone"]["required_ids"]),
            "materials": {"active_plan": retained, "released_plan": released,
                          "temporary_directory_exists_after": temp_path.exists(),
                          "temporary_bytes_reclaimed": sum(m["bytes"] for m in materials)},
            "capacity": {"free_before": free_before, "free_after": shutil.disk_usage(ROOT).free,
                         "minimum_free": MIN_FREE, "planned_peak": PEAK_BYTES, "reserve": RESERVE_BYTES},
            "release_preparation": "ready-for-review" if aggregate == "pass" else "blocked",
            "independent_review": "not-run", "actual_project_acceptance": "not-run",
            "adoption": "not-decided", "publication": "not-applicable", "deployment": "not-applicable"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, default=RECORD)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--input-sha256")
    parser.add_argument("--output-sha256")
    parser.add_argument("--max-input-bytes", type=int, default=MAX_INPUT_BYTES)
    args = parser.parse_args()
    try:
        if args.source is not None:
            g.need(args.target is not None and args.input_sha256 and args.output_sha256,
                   "conversion requires target and both preselected hashes")
            result = convert_csv(args.source, args.target, args.input_sha256,
                                 args.output_sha256, max_input_bytes=args.max_input_bytes)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        record = load_json(args.record)
        result = validate_record(record) if args.validate_only else run_example(record)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0 if args.validate_only or result["aggregate"] == "pass" else 1
    except (ValueError, AssertionError, OSError, KeyError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
