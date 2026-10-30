"""Current finite cloud predicate checks; archived 32-case review mappings are verified separately."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from examples.cloud_contracts import case_predicates as oracle
from examples.cloud_contracts.contracts import ContractError


class CorrectedPredicateTests(unittest.TestCase):
    def test_payload_identity_uses_observed_utf8_bytes_not_a_tag_label(self):
            payload = '合成构建物甲'
            sha = hashlib.sha256(payload.encode()).hexdigest()
            self.assertEqual(oracle.content_identity(payloads=[payload], recorded_digests=[sha]), 'identified')
            with self.assertRaises(ContractError):
                oracle.content_identity(payloads=[payload + '!'], recorded_digests=[sha])

    def test_root_readonly_allows_an_approved_separate_tmpfs(self):
            self.assertEqual(oracle.rootfs_write(root_readonly_promised=True, writes_to_root=False,
                             write_succeeded=True, approved_separate_volume=True), 'write-boundary-preserved')

    def test_unapproved_separate_write_is_not_hidden_by_readonly_root(self):
            with self.assertRaises(ContractError):
                oracle.rootfs_write(root_readonly_promised=True, writes_to_root=False,
                                    write_succeeded=True, approved_separate_volume=False)

    def test_irreversible_exact_approved_plan_may_be_automated(self):
            plan = hashlib.sha256(b'synthetic irreversible plan').hexdigest()
            for classification, approval, protected in [(False, plan, True), (True, '0' * 64, True),
                                                       (True, plan, False)]:
                with self.subTest(classification=classification, approval=approval, protected=protected):
                    with self.assertRaises(ContractError):
                        oracle.classified_change(plan_digest=plan, approved_plan_digest=approval,
                            irreversible=True, irreversible_classified=classification,
                            protection_satisfied=protected)
            self.assertEqual(oracle.classified_change(plan_digest=plan, approved_plan_digest=plan,
                irreversible=True, irreversible_classified=True, protection_satisfied=True), 'authorized-in-fixture')

    def test_revocation_deadline_is_inclusive_and_earlier_real_denial_is_legal(self):
            with self.assertRaises(ContractError):
                oracle.revocation_window(observed_at=60, revoke_deadline=60,
                                         write_allowed=True, reported_revoked=False)
            self.assertEqual(oracle.revocation_window(observed_at=1, revoke_deadline=60,
                             write_allowed=False, reported_revoked=True), 'observed-denied')

    def test_revocation_completion_cannot_be_claimed_even_inside_window(self):
            with self.assertRaises(ContractError):
                oracle.revocation_window(observed_at=1, revoke_deadline=60,
                                         write_allowed=True, reported_revoked=True)

    def test_outage_inside_budget_still_cannot_be_reported_healthy(self):
            with self.assertRaises(ContractError):
                oracle.outage_promise(outage_duration=1, approved_outage_limit=30,
                                      service_available=False, reported_healthy=True)

    def test_recovery_duration_equal_to_approved_limit_is_legal(self):
            self.assertEqual(oracle.outage_promise(outage_duration=30, approved_outage_limit=30,
                service_available=False, reported_healthy=False), 'within-promise-honest')

    def test_missing_proof_can_be_honestly_blocked(self):
            self.assertEqual(oracle.proof_consumption(proof_required=True, proof_verified=False,
                consumption_allowed=False, referrers_supported=False, discovery='none'), 'consumption-blocked')

    def test_optional_proof_does_not_become_a_universal_requirement(self):
            self.assertEqual(oracle.proof_consumption(proof_required=False, proof_verified=False,
                consumption_allowed=True, referrers_supported=False, discovery='none'), 'consumption-allowed')

    def test_unsupported_api_cannot_be_the_observed_proof_source(self):
            with self.assertRaises(ContractError):
                oracle.proof_consumption(proof_required=True, proof_verified=True,
                    consumption_allowed=True, referrers_supported=False, discovery='referrers-api')

    def test_withdrawal_does_not_require_deleting_evidence_storage(self):
            payload = 'withdrawn fixture'
            sha = hashlib.sha256(payload.encode()).hexdigest()
            for retained in [False, True]:
                self.assertEqual(oracle.withdrawal_consumption(payload=payload, denied_digests=[sha],
                    consumption_allowed=False, retained_in_storage=retained), 'withdrawal-policy-preserved')

    def test_nonfinite_or_boolean_time_cannot_enter_deadline_comparison(self):
            for value in [True, float('nan'), float('inf'), -1, '60']:
                with self.subTest(value=value):
                    with self.assertRaises(ContractError):
                        oracle.revocation_window(observed_at=value, revoke_deadline=60,
                                                 write_allowed=False, reported_revoked=False)

    def test_large_exact_integer_is_not_rejected_by_float_conversion(self):
            self.assertEqual(oracle.outage_promise(outage_duration=1,
                approved_outage_limit=10**1000, service_available=False,
                reported_healthy=False), 'within-promise-honest')

    def test_unknown_dispatch_and_observation_fields_are_not_ignored(self):
            with self.assertRaises(ContractError):
                oracle.evaluate('not-a-real-oracle', {})
            with self.assertRaises(ContractError):
                oracle.evaluate('completion-report', {'actually_complete': True,
                                                      'reported_complete': True, 'ignored_override': True})

    def mutated_module(self, before, after):
            source = (ROOT / 'examples/cloud_contracts/case_predicates.py').read_text()
            self.assertEqual(source.count(before), 1)
            module = types.ModuleType('examples.cloud_contracts.mutated_predicates')
            module.__package__ = 'examples.cloud_contracts'
            exec(compile(source.replace(before, after, 1), '<isolated-semantic-mutant>', 'exec'), module.__dict__)
            return module

    def test_planned_rotation_interruption_is_not_a_universal_failure(self):
            valid=dict(service_available=False,controlled_recovery=True,outage_duration=10,
                       approved_outage_limit=30,reported_cutover_complete=False)
            self.assertEqual(oracle.rotation_interruption(**valid),'cutover-observation-pending')
            for change in ({'controlled_recovery':False},{'outage_duration':31},
                           {'reported_cutover_complete':True}):
                with self.subTest(change=change),self.assertRaises(ContractError):
                    oracle.rotation_interruption(**dict(valid,**change))
            self.assertEqual(oracle.rotation_interruption(**dict(valid,outage_duration=30)),
                             'cutover-observation-pending')

    def test_forced_termination_must_preserve_every_accepted_operation(self):
            base=dict(accepted_operations=['one','two'],completed_operations=['one'],
                      recoverable_operations=['two'],reported_clean_completion=False,forced_kill=True)
            self.assertEqual(oracle.termination_accounting(**base),'recovery-pending')
            self.assertEqual(oracle.termination_accounting(**dict(base,
                completed_operations=['one','two'],recoverable_operations=[],reported_clean_completion=True)),
                'termination-complete-accounted')
            for change in ({'recoverable_operations':[]},{'reported_clean_completion':True},
                           {'completed_operations':['one','alien']},{'accepted_operations':['one','one']}):
                with self.subTest(change=change),self.assertRaises(ContractError):
                    oracle.termination_accounting(**dict(base,**change))
            self.assertEqual(oracle.termination_accounting(accepted_operations=[],completed_operations=[],
                recoverable_operations=[],reported_clean_completion=True,forced_kill=True),
                'termination-complete-accounted')

    def test_unknown_recovery_cannot_be_mutated_into_clean_completion(self):
            observation=dict(accepted_operations=['one'],completed_operations=[],recoverable_operations=['one'],
                             reported_clean_completion=True,forced_kill=True)
            with self.assertRaises(ContractError):oracle.termination_accounting(**observation)
            changed=self.mutated_module(
                'not reported_clean_completion or set(accepted_operations) <= set(completed_operations)',
                'True')
            self.assertEqual(changed.termination_accounting(**observation),'recovery-pending')

    def test_single_writer_and_supported_coordinated_multiwriter_are_distinct(self):
            single=dict(protocol='single-writer',authorized_writers=['current'],
                        observed_writers=['current'],coordination_verified=False)
            self.assertEqual(oracle.writer_admission(**single),'writer-protocol-preserved')
            for change in ({'observed_writers':['old','current']},
                           {'authorized_writers':['current','old']},{'protocol':'unknown'}):
                with self.subTest(change=change),self.assertRaises(ContractError):
                    oracle.writer_admission(**dict(single,**change))
            multiple=dict(protocol='coordinated-multiwriter',authorized_writers=['a','b'],
                          observed_writers=['a','b'],coordination_verified=True)
            self.assertEqual(oracle.writer_admission(**multiple),'writer-protocol-preserved')
            with self.assertRaises(ContractError):
                oracle.writer_admission(**dict(multiple,coordination_verified=False))

    def test_projected_file_version_is_not_process_environment_version(self):
            self.assertEqual(oracle.secret_refresh(published_version='v2', projected_version='v2',
                consumer_version='v1', observed_at=10, refresh_deadline=60,
                reported_refreshed=False), 'consumer-refresh-pending')
            with self.assertRaises(ContractError):
                oracle.secret_refresh(published_version='v2', projected_version='v2',
                    consumer_version='v1', observed_at=60, refresh_deadline=60,
                    reported_refreshed=False)

    def test_actual_premature_current_promotion_fails_even_without_completion_claim(self):
            with self.assertRaises(ContractError):
                oracle.rotation_stage(notification_received=True, candidate_created=True,
                    target_set=False, target_tested=False, current_promoted=True,
                    consumers_updated=False, old_revoked=False, reported_stage='awaiting')

    def test_unknown_rotation_stage_is_not_silently_treated_as_pending(self):
            with self.assertRaises(ContractError):
                oracle.rotation_stage(notification_received=False, candidate_created=False,
                    target_set=False, target_tested=False, current_promoted=False,
                    consumers_updated=False, old_revoked=False, reported_stage='made-up-success')

    def test_unknown_or_repeated_scopes_cannot_be_claimed_complete(self):
            for scopes in [['not-observed'], ['http', 'http'], ['queue']]:
                with self.assertRaises(ContractError):
                    oracle.scoped_completion(observations={'http': 'complete', 'queue': 'unknown'},
                                             reported_complete_scopes=scopes)
            self.assertEqual(oracle.scoped_completion(
                observations={'http': 'complete', 'queue': 'unknown'},
                reported_complete_scopes=['http']), 'scoped-report-consistent')

    def test_incident_evidence_cannot_be_erased_behind_silence(self):
            with self.assertRaises(ContractError):
                oracle.incident_facts(silence_active=True, failure_observed=True,
                                      incident_recorded=False, reported_resolved=False)

    def test_required_backup_object_must_exist_even_when_omitted_from_claim(self):
            with self.assertRaises(ContractError):
                oracle.backup_scope(backed_objects=['yaml'], claimed_objects=['yaml'],
                                    required_objects=['yaml', 'pv'])

    def test_cost_sum_is_exact_instead_of_binary_float_or_decimal_context_rounding(self):
            n='1234567890123456789012345678901234567890.1'
            total='1234567890123456789012345678901234567890.3'
            resources=[{'id':'a','present':True,'owner':'owner','observed_cost':n,'recorded_cost':n},
                       {'id':'b','present':True,'owner':'owner','observed_cost':'0.2','recorded_cost':'0.2'}]
            self.assertEqual(oracle.retirement_resources(resources=resources, claimed_deleted=[],
                reported_total_cost=total), 'retirement-state-and-cost-consistent')
            with self.assertRaises(ContractError):
                oracle.retirement_resources(resources=resources, claimed_deleted=[],
                                             reported_total_cost='1234567890123456789012345678901234567890')

    def test_fixture_money_bounds_and_nonfinite_rejections_are_explicit(self):
            for value in ['NaN', 'Infinity', '-1', '1e1000000000', '0.'+'0'*12+'1', True, 0.1]:
                with self.subTest(value=value):
                    with self.assertRaises(ContractError):
                        oracle.cost_value(value)
            self.assertEqual(oracle.cost_value('0.000000000001').denominator, 10**12)

    def test_retained_object_needs_owner_and_actual_cost_even_after_state_removal(self):
            row={'id':'kept','present':True,'owner':'','observed_cost':'1','recorded_cost':'1'}
            with self.assertRaises(ContractError):
                oracle.retirement_resources(resources=[row], claimed_deleted=[], reported_total_cost='1')
            row['owner']='current-owner'
            with self.assertRaises(ContractError):
                oracle.retirement_resources(resources=[row], claimed_deleted=[], reported_total_cost='0')

    def test_active_callback_needs_current_owner_and_authorization(self):
            for authorized, owner in [(False, 'owner'), (True, '')]:
                with self.subTest(authorized=authorized, owner=owner):
                    with self.assertRaises(ContractError):
                        oracle.external_exit(active_integrations=[{'id':'callback','authorized':authorized,
                            'owner':owner}], reported_fully_retired=False)

if __name__ == '__main__':
    unittest.main()
