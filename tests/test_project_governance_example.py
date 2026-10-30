"""Direct parser, record-semantic, state-recovery and bounded mutation tests."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tests.platform_support import make_symlink
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "examples/project-governance/project_example.py"
SPEC = importlib.util.spec_from_file_location("project_governance_example", PATH)
example = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(example)
g = example.g


class CsvRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="governance-test-", dir=ROOT.parent)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "input.csv"
        self.target = self.directory / "output.csv"
        self.raw = "name,id\n安,1\nBo,2\n".encode()
        self.expected = "id,name\n1,安\n2,Bo\n".encode()
        self.source.write_bytes(self.raw)

    def convert(self, raw=None, expected=None, **kwargs):
        raw = self.raw if raw is None else raw
        expected = self.expected if expected is None else expected
        self.source.write_bytes(raw)
        return example.convert_csv(self.source, self.target,
                                   example.digest(raw), example.digest(expected), **kwargs)

    def assert_no_partial_output(self, raw):
        self.assertEqual(self.source.read_bytes(), raw)
        self.assertFalse(self.target.exists())
        self.assertEqual(list(self.directory.glob(".csv-*")), [])

    def test_normal_bytes_and_original_identity(self):
        result = self.convert()
        self.assertEqual(self.target.read_bytes(), self.expected)
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertEqual(result["output_sha256"], example.digest(self.expected))
        self.assertEqual(result["input_bytes"], len(self.raw))

    def test_late_bad_row_rejected_in_parser_not_hash_prefilter(self):
        raw = self.raw + b"broken\n"
        with self.assertRaisesRegex(example.ConversionError, "^row-width$"):
            self.convert(raw)
        self.assert_no_partial_output(raw)

    def test_direct_bad_inputs_reach_distinct_parser_rules(self):
        cases = [(b"name,id\nA,0\n", "id-format"),
                 (b"name,id\nA,01\n", "id-format"),
                 (b"name,id\nA,1\nB,1\n", "duplicate-id"),
                 (b"name,id\n ,1\n", "empty-name"),
                 (b"name,id\nA,1,extra\n", "row-width"),
                 (b'name,id\n"unterminated,1\n', "csv-syntax"),
                 (b"id,name\n1,A\n", "header"),
                 (b"name,id\nA\x00,1\n", "nul-character"),
                 (b"name,id\n\xff,1\n", "encoding"),
                 (b"\xef\xbb\xbfname,id\nA,1\n", "header")]
        for raw, reason in cases:
            with self.subTest(reason=reason, raw=raw):
                with self.assertRaisesRegex(example.ConversionError, "^" + reason + "$"):
                    self.convert(raw)
                self.assert_no_partial_output(raw)

    def test_legal_header_only_quoted_crlf_and_no_final_newline_neighbors(self):
        cases = [(b"name,id\n", b"id,name\n"),
                 (b"name,id\r\nA,1\r\n", b"id,name\n1,A\n"),
                 (b'name,id\n"A,B",1\n', b'id,name\n1,"A,B"\n'),
                 (b'name,id\n"A\nB",1\n', b'id,name\n1,"A\nB"\n'),
                 (b'name,id\n"A""B",1\n', b'id,name\n1,"A""B"\n'),
                 (b"name,id\n A ,1", b"id,name\n1, A \n")]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(example.encode_output(raw), expected)

    def test_exact_size_boundary_and_invalid_limit(self):
        self.assertEqual(example.encode_output(self.raw, len(self.raw)), self.expected)
        with self.assertRaisesRegex(example.ConversionError, "input-too-large"):
            self.convert(max_input_bytes=len(self.raw) - 1)
        self.assert_no_partial_output(self.raw)
        for limit in [True, -1, 0, example.MAX_INPUT_BYTES + 1]:
            with self.subTest(limit=limit), self.assertRaisesRegex(example.ConversionError, "input-limit"):
                self.convert(max_input_bytes=limit)

    def test_large_legal_field_at_limit_is_not_rejected_by_library_default(self):
        name = b"x" * (example.MAX_INPUT_BYTES - len(b"name,id\n,1\n"))
        raw = b"name,id\n" + name + b",1\n"
        expected = b"id,name\n1," + name + b"\n"
        old_limit = example.csv.field_size_limit()
        self.assertEqual(len(raw), example.MAX_INPUT_BYTES)
        self.assertEqual(example.encode_output(raw), expected)
        self.assertEqual(example.csv.field_size_limit(), old_limit)
        with self.assertRaisesRegex(example.ConversionError, "input-too-large"):
            example.encode_output(raw + b"\n")

    def test_wrong_input_and_output_identities_preserve_original(self):
        good_input, good_output = example.digest(self.raw), example.digest(self.expected)
        for ih, oh, error in [(example.digest(b"other"), good_output, "input-identity"),
                              (good_input, example.digest(b"other"), "output-identity")]:
            with self.subTest(error=error):
                with self.assertRaisesRegex(example.ConversionError, error):
                    example.convert_csv(self.source, self.target, ih, oh)
                self.assert_no_partial_output(self.raw)

    def test_same_path_and_existing_target_are_not_overwritten(self):
        with self.assertRaisesRegex(example.ConversionError, "same-path"):
            example.convert_csv(self.source, self.source, example.digest(self.raw), example.digest(self.expected))
        sentinel = b"existing result\n"
        self.target.write_bytes(sentinel)
        with self.assertRaisesRegex(example.ConversionError, "target-exists"):
            self.convert()
        self.assertEqual(self.target.read_bytes(), sentinel)
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_symlink_and_hardlink_neighbors_do_not_overwrite_source(self):
        make_symlink(self.target, self.source)
        with self.assertRaisesRegex(example.ConversionError, "same-path"):
            self.convert()
        self.target.unlink()
        os.link(self.source, self.target)
        with self.assertRaisesRegex(example.ConversionError, "target-exists"):
            self.convert()
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_atomic_target_race_preserves_winner_and_cleans_temporary(self):
        real_link = os.link
        def racing_link(source, target):
            Path(target).write_bytes(b"other writer won\n")
            return real_link(source, target)
        with mock.patch.object(example.os, "link", side_effect=racing_link):
            with self.assertRaisesRegex(example.ConversionError, "target-exists"):
                self.convert()
        self.assertEqual(self.target.read_bytes(), b"other writer won\n")
        self.assertEqual(self.source.read_bytes(), self.raw)
        self.assertFalse(list(self.directory.glob(".csv-*")))

    def test_commit_failure_and_input_change_leave_no_partial_output(self):
        with mock.patch.object(example.os, "link", side_effect=OSError("unsupported")):
            with self.assertRaisesRegex(example.ConversionError, "commit-unavailable"):
                self.convert()
        self.assert_no_partial_output(self.raw)
        real_encode = example.encode_output
        changed = b"name,id\nChanged,9\n"
        def concurrent_change(raw, limit):
            self.source.write_bytes(changed)
            return real_encode(raw, limit)
        with mock.patch.object(example, "encode_output", side_effect=concurrent_change):
            with self.assertRaisesRegex(example.ConversionError, "input-changed"):
                self.convert()
        self.assert_no_partial_output(changed)

    def test_failure_recovery_uses_new_input_and_keeps_existing_files(self):
        bad = self.raw + b"bad\n"
        with self.assertRaisesRegex(example.ConversionError, "row-width"):
            self.convert(bad)
        self.assert_no_partial_output(bad)
        recovered = self.directory / "recovered.csv"
        recovered.write_bytes(self.raw)
        example.convert_csv(recovered, self.target, example.digest(self.raw), example.digest(self.expected))
        self.assertEqual(self.source.read_bytes(), bad)
        self.assertEqual(self.target.read_bytes(), self.expected)

    def test_wrong_serialization_mutation_reaches_output_contract(self):
        with mock.patch.object(example, "encode_output", return_value=self.raw):
            with self.assertRaisesRegex(example.ConversionError, "output-identity"):
                self.convert()
        self.assert_no_partial_output(self.raw)


class ProjectRecordTests(unittest.TestCase):
    def setUp(self):
        self.record = example.load_json(example.RECORD)

    def test_schema_filled_record_and_starter_have_distinct_readiness(self):
        result = example.validate_record(self.record)
        self.assertEqual(result["check_aggregate"], "not-run")
        self.assertEqual(result["readiness"], "contracts-defined")
        starter = example.load_json(ROOT / "templates/project-governance/project-record.template.json")
        self.assertEqual(example.validate_record(starter)["readiness"], "not-ready")
        starter["record_state"] = "planned"
        with self.assertRaisesRegex(ValueError, "planned record"):
            example.validate_record(starter)

    def test_schema_rejects_extra_missing_boolean_and_unsupported_keyword(self):
        schema = example.load_json(example.SCHEMA)
        for mutate in [lambda r: r.update(extra=True), lambda r: r.pop("requirements"),
                       lambda r: r["project"]["scope"].update(revision=True)]:
            changed = copy.deepcopy(self.record)
            mutate(changed)
            with self.subTest(mutation=mutate), self.assertRaises(AssertionError):
                example.schema_check(changed, schema)
        with self.assertRaisesRegex(AssertionError, "unsupported schema keyword"):
            example.schema_check({}, {"type": "object", "oneOf": []})

    def test_direct_semantic_mutations_are_not_blocked_by_record_hash(self):
        cases = [(lambda r: r["checks"]["required_ids"].pop(), "exactly cover"),
                 (lambda r: r["project"]["fixtures"].append(copy.deepcopy(r["project"]["fixtures"][0])), "fixtures must be unique"),
                 (lambda r: r["work_items"][0]["acceptance_ids"].append(r["work_items"][0]["acceptance_ids"][0]), "work acceptance must be unique"),
                 (lambda r: r["requirements"][0].update(scope_id="cloud-sync"), "requirement outside"),
                 (lambda r: r["acceptance"][0].update(requirement_id="missing"), "back-reference"),
                 (lambda r: r["requirements"][0].update(implementation_symbol="missing"), "symbol not found"),
                 (lambda r: r["adoption"].update(scope_ids=["production-deployment"]), "adoption scope outside"),
                 (lambda r: r["work_items"][0].update(dependencies=["missing-item"]), "missing required dependency"),
                 (lambda r: r["adoption"]["selections"][0]["clauses"][0].update(id="PGF-99"), "unknown selected clause"),
                 (lambda r: r["project"]["lifecycle"].update(state="accepted"), "accepted milestone/project"),
                 (lambda r: r["requirements"][0].update(state="verified"), "verified requirement"),
                 (lambda r: r["change"].update(independent_review="pass"), "independent review")]
        for mutate, expected in cases:
            changed = copy.deepcopy(self.record)
            mutate(changed)
            # Shape remains legal: failures must enter the intended semantic checks.
            example.schema_check(changed, example.load_json(example.SCHEMA))
            with self.subTest(expected=expected), self.assertRaisesRegex(ValueError, expected):
                example.validate_record(changed)

    def test_legal_text_and_scope_subset_neighbors(self):
        self.record["project"]["scope"]["in_scope"].append("documentation")
        self.record["project"]["problem"] += " 此次仅修正描述措辞。"
        self.assertEqual(example.validate_record(self.record)["record_consistency"], "pass")
        self.assertEqual(self.record["adoption"]["scope_ids"], ["offline-csv"])

    def test_dependency_lock_failure_and_recovery(self):
        changed = copy.deepcopy(self.record)
        changed["dependencies"]["records"][0]["locked_version"] = "999"
        with self.assertRaisesRegex(ValueError, "resolved/locked version drift"):
            example.validate_record(changed)
        self.assertEqual(example.validate_record(self.record)["record_consistency"], "pass")
        changed["dependencies"]["records"].clear()
        with self.assertRaisesRegex(ValueError, "dependency missing"):
            example.validate_record(changed)

    def test_dependency_kind_or_document_substitution_cannot_bypass_identity(self):
        changed = copy.deepcopy(self.record)
        changed["dependencies"]["records"][0]["kind"] = "service"
        with self.assertRaisesRegex(ValueError, "only resolves standards"):
            example.validate_record(changed)
        changed = copy.deepcopy(self.record)
        changed["dependencies"]["records"][0]["path"] = changed["dependencies"]["records"][1]["path"]
        with self.assertRaisesRegex(ValueError, "dependency document identity drift"):
            example.validate_record(changed)

    def test_field_reference_contains_every_finite_schema_leaf(self):
        def leaves(schema, path=""):
            if schema.get("type") == "object" and "properties" in schema:
                for key, child in schema["properties"].items():
                    yield from leaves(child, path + "." + key if path else key)
            elif schema.get("type") == "array" and "properties" in schema.get("items", {}):
                yield from leaves(schema["items"], path + "[]")
            else:
                yield path
        documentation = (ROOT / "templates/project-governance/README.md").read_text(encoding="utf-8")
        for path in leaves(example.load_json(example.SCHEMA)):
            with self.subTest(path=path):
                self.assertIn("`" + path + "`", documentation)

    def test_unknown_cannot_be_relabelled_as_pass_without_evidence(self):
        self.record["checks"]["results"] = [{"id": "CSV-01", "state": "pass",
            "candidate_sha256": "a" * 64, "evidence": []}]
        with self.assertRaisesRegex(ValueError, "needs evidence"):
            example.validate_record(self.record)

    def test_imported_results_bind_to_actual_source_identity(self):
        identity = example.capture_source_identity(ROOT)
        self.record['checks']['results'] = [{
            'id': 'CSV-01', 'state': 'pass',
            'candidate_sha256': g.canonical_hash(identity),
            'evidence': ['synthetic-test:original-conversion-observation']}]
        self.assertEqual(example.validate_record(self.record)['record_consistency'], 'pass')
        self.record['checks']['results'][0]['candidate_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'candidate identity is stale or mixed'):
            example.validate_record(self.record)

    def test_no_fake_attribution_or_real_authorization_in_synthetic_record(self):
        self.record["adoption"]["decision"]["actor"] = "example-owner"
        with self.assertRaisesRegex(ValueError, "undecided cannot invent"):
            example.validate_record(self.record)
        self.record["adoption"]["decision"] = {"state": "approved", "actor": "example-owner",
                                                "at": "2026-10-24T00:00:00Z", "reference": "made-up"}
        with self.assertRaisesRegex(ValueError, "synthetic record cannot claim"):
            example.validate_record(self.record)

    def test_json_duplicate_keys_and_nonfinite_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="record-parser-", dir=ROOT.parent) as tmp:
            p = Path(tmp) / "record.json"
            for raw, expected in [("{\"id\":1,\"id\":2}", "duplicate JSON key"),
                                  ("{\"value\":NaN}", "nonfinite JSON")]:
                p.write_text(raw)
                with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, expected):
                    example.load_json(p)


    def test_canonical_level_three_clause_selection_is_a_legal_neighbor(self):
        registry={row['id']:row for row in example.load_json(ROOT/'registry/standards.json')}
        old=self.record['adoption']['selections'][0]['document_id']
        selected=registry['STD-PG-005']
        self.record['adoption']['selections'][0].update(
            document_id=selected['id'],path=selected['path'],version=selected['version'],sha256=selected['sha256'])
        self.record['adoption']['selections'][0]['clauses']=[{
            'id':'PGE-02','applicability':'applicable','reason':'Synthetic check of canonical ### clause selection.',
            'acceptance_ids':[], 'automated_scope':[], 'manual_criteria':['Inspect the README version, license and security entry semantics.'], 'manual_state':'not-run','manual_evidence':[]}]
        self.record['adoption']['dependency_bindings']=[b for b in self.record['adoption']['dependency_bindings']if b['from_document']!=old]
        dependency=next(row for row in self.record['dependencies']['records'] if row['id']==old)
        dependency.update(id=selected['id'],path=selected['path'],
                          locked_version=selected['version'],expected_sha256=selected['sha256'])
        self.assertEqual(example.validate_record(self.record)['record_consistency'],'pass')
        self.record['adoption']['selections'][0]['clauses'][0]['id']='PGE-99'
        with self.assertRaisesRegex(ValueError,'unknown selected clause'):
            example.validate_record(self.record)

    def test_proposed_trial_deviation_is_not_an_approved_formal_exception(self):
        selection=self.record['adoption']['selections'][0]
        exception={'id':'EX-SYNTHETIC','requirement_id':self.record['requirements'][0]['id'],
            'document_sha256':selection['sha256'],'scope':'offline-csv','reason':'Synthetic boundary record.',
            'state':'proposed','starts_at':'2026-10-24T00:00:00Z','expires_at':'2026-10-25T00:00:00Z',
            'review_triggered':False,'compensations':[{'id':'compensation','state':'not-run'}],
            'recovery':'Keep the original condition blocked until a valid decision.', 'decision':{'state':'not-decided'}}
        self.record['adoption']['exceptions']=[exception]
        self.assertEqual(example.validate_record(self.record)['record_consistency'],'pass')
        self.record['example_only']=False
        exception.update(state='approved',decision={'state':'approved','actor':'synthetic-test-actor',
            'at':'2026-10-24T00:00:00Z','reference':'synthetic:test-only'})
        with self.assertRaisesRegex(ValueError,'formal exception requires an adopted project obligation'):
            example.validate_record(self.record)


class ModelBoundaryAndExecutionTests(unittest.TestCase):
    def setUp(self):
        self.record = example.load_json(example.RECORD)

    def test_all_predeclared_contracts_run_and_temporary_data_is_released(self):
        before = copy.deepcopy(self.record)
        result = example.run_example(self.record)
        self.assertEqual(result["aggregate"], "pass")
        self.assertTrue(all(x["state"] == "pass" for x in result["requirement_results"]))
        self.assertTrue(all(x["state"] == "pass" for x in result["success_results"]))
        self.assertEqual(len(result["observations"]), len(self.record["acceptance"]))
        self.assertTrue(result["milestone_ready_in_model"])
        self.assertFalse(result["materials"]["temporary_directory_exists_after"])
        self.assertTrue(result["source_unchanged"])
        self.assertEqual(result['candidate_sha256'], g.canonical_hash(result['source_identity']))
        self.assertEqual(self.record, before)
        self.assertEqual(result["actual_project_acceptance"], "not-run")
        self.assertEqual(result["independent_review"], "not-run")
        csv_results = [x for x in result["observations"] if x["contract"]["layer"] == "isolated-runtime"]
        self.assertTrue(all("process_exit_code" in x["file_identities"] for x in csv_results))
        self.assertTrue(all(x["event"]["exit_code"] == x["file_identities"]["process_exit_code"] for x in csv_results))
        self.assertTrue(any(x["event"]["exit_code"] == 2 for x in csv_results))

    def test_bad_independent_expectation_yields_failure_not_closed_work(self):
        self.record["acceptance"][0]["expected_value"]["output_text"] = "wrong independent expectation"
        result = example.run_example(self.record)
        self.assertEqual(result["aggregate"], "fail")
        self.assertEqual(result["requirement_results"][0]["state"], "fail")
        self.assertFalse(result["milestone_ready_in_model"])
        self.assertEqual(result["work_items"][0]["state"], "verification")
        self.assertEqual(result["release_preparation"], "blocked")

    def test_false_green_aggregation_mutation_is_detected_at_result_comparison(self):
        with mock.patch.object(g, "aggregate_checks", return_value="pass"):
            exit_code, actual = example._model_observation("missing-check", self.record)
        contract = {"id": "mutation", "input_sha256": "a" * 64, "environment_sha256": "b" * 64,
                    "layer": "finite-model", "expectation_origin": "requirement", "expected_exit": 0,
                    "expected_value": {"state": "partial"}}
        event = {k: contract[k] for k in ("id", "input_sha256", "environment_sha256", "layer")}
        event.update(completion="completed", exit_code=exit_code, actual=actual)
        self.assertEqual(g.evaluate_check(contract, event), "fail")

    def test_stale_work_revision_rejected_then_valid_transition_preserves_history(self):
        item = self.record["work_items"][0]
        with self.assertRaisesRegex(ValueError, "stale work revision"):
            example.transition_item(item, "triaged", 1)
        next_item = example.transition_item(item, "triaged", 0)
        self.assertEqual(next_item["revision"], 1)
        self.assertEqual(next_item["history"], [{"from": "open", "to": "triaged", "revision": 1}])
        self.assertEqual(item["state"], "open")
        with self.assertRaisesRegex(ValueError, "invalid work-item transition"):
            example.transition_item(next_item, "verification", 1)

    def test_nonverified_close_preserves_reason_without_claiming_delivery(self):
        item = example.transition_item(self.record["work_items"][0], "triaged", 0)
        closed = example.transition_item(item, "closed", 1, resolution="not-reproducible",
                                         reason="specified synthetic input does not reproduce the report")
        self.assertIn("reason", closed["history"][-1])
        self.assertFalse(g.milestone_ready([closed], [closed["id"]]))

    def test_blocked_work_can_resume_but_unknown_evidence_cannot_close(self):
        item = self.record["work_items"][0]
        for target in ["triaged", "in-progress", "blocked", "in-progress", "verification"]:
            item = example.transition_item(item, target, item["revision"])
        unknown = {x: "unknown" for x in item["acceptance_ids"]}
        with self.assertRaisesRegex(ValueError, "lacks exact passed"):
            example.transition_item(item, "closed", item["revision"],
                                    resolution="verified-delivery", evidence=unknown)
        closed = example.transition_item(item, "closed", item["revision"],
                        resolution="verified-delivery", evidence={x: "pass" for x in item["acceptance_ids"]})
        reopened = example.transition_item(closed, "triaged", closed["revision"])
        self.assertEqual(closed["resolution"], "verified-delivery")
        self.assertIsNone(reopened["resolution"])

    def test_model_unknown_missing_failure_and_recovery_remain_distinct(self):
        expected = {"missing-check": "partial", "failed-check": "fail", "unknown-check": "unknown", "recovery": "pass"}
        for scenario, state in expected.items():
            with self.subTest(scenario=scenario):
                _, actual = example._model_observation(scenario, self.record)
                self.assertEqual(actual["state"], state)
        self.assertEqual(example._model_observation("recovery", self.record)[1]["original_state"], "unknown")

    def test_event_identity_and_completion_are_not_interchangeable(self):
        contract = {"id": "check", "input_sha256": "a" * 64, "environment_sha256": "b" * 64,
                    "layer": "isolated-runtime", "expectation_origin": "requirement",
                    "expected_exit": 0, "expected_value": {"value": 1}}
        event = {k: contract[k] for k in ("id", "input_sha256", "environment_sha256", "layer")}
        event.update(completion="timed-out", exit_code=0, actual={"value": 1})
        self.assertEqual(g.evaluate_check(contract, event), "unknown")
        event["completion"] = "skipped"
        self.assertEqual(g.evaluate_check(contract, event), "not-run")
        event["input_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "drift"):
            g.evaluate_check(contract, event)

    def test_typed_json_adapter_rejects_bool_number_mutation_and_accepts_neighbor(self):
        contract = {"id": "typed-json", "input_sha256": "a" * 64, "environment_sha256": "b" * 64,
                    "layer": "finite-model", "expectation_origin": "requirement",
                    "expected_exit": 0, "expected_value": {"count": 0, "ok": True}}
        event = {k: contract[k] for k in ("id", "input_sha256", "environment_sha256", "layer")}
        event.update(completion="completed", exit_code=0, actual={"count": False, "ok": 1})
        self.assertEqual(example.evaluate_observation(contract, event), "fail")
        event["actual"] = {"ok": True, "count": 0}
        self.assertEqual(example.evaluate_observation(contract, event), "pass")
        self.assertEqual(example.evaluate_observation(contract, None), "not-run")

    def test_subprocess_timeout_preserves_captured_output_and_unknown_state(self):
        with tempfile.TemporaryDirectory(prefix="governance-timeout-", dir=ROOT.parent) as tmp:
            timeout = subprocess.TimeoutExpired("synthetic command", 30,
                                                output=b"partial raw output", stderr=b"timeout detail")
            with mock.patch.object(example.subprocess, "run", side_effect=timeout):
                code, actual, evidence = example._csv_observation("normal", self.record, Path(tmp))
            self.assertIsNone(code)
            self.assertEqual(evidence["completion"], "timed-out")
            self.assertEqual(evidence["stdout"], "partial raw output")
            self.assertEqual(evidence["stderr"], "timeout detail")
            self.assertTrue(actual["input_unchanged"])

    def test_material_reference_revision_and_holds_block_reclaim(self):
        row = {"id": "cache", "path": "cache.bin", "kind": "cache", "bytes": 1,
               "sha256": example.digest(b"x"), "dependencies": [], "holds": [],
               "rebuild_inputs_available": True, "rebuild_command": "rebuild synthetic x"}
        self.assertFalse(g.reclaim_plan([row], ["cache"], 0, 0)["reclaimable"])
        with self.assertRaisesRegex(ValueError, "revision changed"):
            g.reclaim_plan([row], [], 0, 1)
        self.assertEqual(len(g.reclaim_plan([row], [], 1, 1)["reclaimable"]), 1)
        for bad_path in [".", "", "./", "cache/..", "cache/./item", "cache/\x00item"]:
            with self.subTest(path=bad_path), self.assertRaisesRegex(ValueError, "unsafe reclaim path"):
                g.reclaim_plan([dict(row, path=bad_path)], [], 1, 1)
        self.assertEqual(g.reclaim_plan([dict(row, path="cache/item")], [], 1, 1)["reclaimable"][0]["path"], "cache/item")
        row["holds"] = ["investigation"]
        self.assertFalse(g.reclaim_plan([row], [], 1, 1)["reclaimable"])

    def test_cli_rejects_optimization_instead_of_disabling_validation(self):
        result = subprocess.run([sys.executable, "-B", "-O", str(PATH), "--validate-only"],
                                cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("without -O/-OO", result.stderr)


if __name__ == "__main__":
    unittest.main()
