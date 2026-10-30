"""Current bounded model-research predicates and synthetic computation/recovery examples."""
import sys
if sys.flags.optimize:raise RuntimeError('optimized mode is not a valid validation run')
from pathlib import Path
import copy,hashlib,json,random,unittest,re
from fractions import Fraction, Fraction as F
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'checks'))
from model_research_finite import *

REQUIRED=('parameters','momentum','rng','scaler','schedule','cursor','contribution_ledger')
def snapshot():
    values={'parameters':[F(5,2)],'momentum':[F(1,2)],'rng':{'position':7},'scaler':{'scale':16},'schedule':{'accepted':6,'tokens':7},'cursor':8,'contribution_ledger':{'consumed':list(range(1,8)),'accepted':list(range(1,7)),'rejected':[7]}}
    return {'id':'snapshot-cut7','cut':7,'complete':True,'uploaded':True,'components':{k:{'cut':7,'value':v} for k,v in values.items()}}

def event(op='all-reduce',root=0,shape=(2,),group='g',generation=1):
    return {'generation':generation,'group':group,'sequence':1,'operation':op,'root':root,'shape':shape}


class FutureSplitTests(unittest.TestCase):
    def records(self, prediction=13):
        return [{'group': 'same-person', 'role': 'train', 'event_at': 3, 'available_at': 4, 'label_available_at': 5},
                {'group': 'same-person', 'role': 'test', 'event_at': 12, 'available_at': 4, 'prediction_at': prediction}]

    def test_training_cutoff_after_prediction_is_rejected(self):
        records = self.records(5); records[0].update(event_at=10, available_at=10, label_available_at=10)
        with self.assertRaisesRegex(ContractError, 'cutoff after'): check_split(records, 'same-subject-future', 10)

    def test_declared_cutoff_not_just_latest_present_row_must_precede_prediction(self):
        with self.assertRaisesRegex(ContractError, 'cutoff after'): check_split(self.records(5), 'same-subject-future', 10)

    def test_later_same_subject_prediction_is_a_legal_neighbor(self):
        self.assertEqual(check_split(self.records(), 'same-subject-future', 10), 'same-subject-future')

    def test_equality_at_cutoff_is_explicitly_legal(self):
        records = self.records(10); records[0].update(event_at=10, available_at=10, label_available_at=10)
        records[1]['available_at'] = 10
        self.assertEqual(check_split(records, 'same-subject-future', 10), 'same-subject-future')

    def test_every_evaluation_prediction_is_checked(self):
        records = self.records(); records.append(dict(records[1], prediction_at=9))
        with self.assertRaisesRegex(ContractError, 'cutoff after'): check_split(records, 'same-subject-future', 10)

    def test_feature_label_and_backfill_guards_remain_distinct(self):
        for index, field, value in ((0, 'event_at', 11), (0, 'available_at', 11),
                                    (0, 'label_available_at', 11), (1, 'available_at', 14)):
            records = self.records(); records[index][field] = value
            with self.subTest(field=field), self.assertRaises(ContractError): check_split(records, 'same-subject-future', 10)

    def test_optional_future_target_must_not_precede_prediction(self):
        for target in (13, 14):
            records = self.records(); records[1]['target_at'] = target
            self.assertEqual(check_split(records, 'same-subject-future', 10), 'same-subject-future')
        records[1]['target_at'] = 12
        with self.assertRaisesRegex(ContractError, 'target precedes'): check_split(records, 'same-subject-future', 10)

    def test_nonfinite_unknown_or_boolean_temporal_coordinates_rejected(self):
        for value in (None, True, '10', float('nan'), float('inf')):
            with self.subTest(value=repr(value)), self.assertRaises(ContractError): check_split(self.records(), 'same-subject-future', value)

    def test_temporal_order_uses_exact_fractional_boundaries(self):
        records = self.records(Fraction(21, 2)); records[1]['available_at'] = Fraction(21, 2)
        self.assertEqual(check_split(records, 'same-subject-future', Fraction(21, 2)), 'same-subject-future')
        with self.assertRaises(ContractError): check_split(records, 'same-subject-future', Fraction(1051, 100))

    def test_cross_subject_and_declared_transductive_claims_not_conflated(self):
        records = self.records()
        with self.assertRaises(ContractError): check_split(records, 'cross-subject')
        records[1]['group'] = 'different-person'
        self.assertEqual(check_split(records, 'cross-subject'), 'cross-subject')
        self.assertEqual(check_split(self.records(), 'transductive', fit_roles=('train', 'test-unlabeled')), 'transductive-not-independent-test')

class PrivacyParameterTests(unittest.TestCase):
    def release(self, identity='release-1', epsilon='1/2'):
        return {'id': identity, 'visible_to': ['observer'], 'epsilon': epsilon, 'unit': 'record'}

    def test_negative_epsilon_cannot_cancel_observed_release(self):
        with self.assertRaisesRegex(ContractError, 'negative epsilon'):
            visible_privacy_ledger([self.release(epsilon=1), self.release('release-2', -1)], 'observer')

    def test_every_visible_mechanism_parameter_is_checked_before_composition(self):
        for epsilon in (-1, '-1/1000', Fraction(-1, 1000000), -0.001):
            with self.subTest(epsilon=epsilon), self.assertRaises(ContractError):
                visible_privacy_ledger([self.release(epsilon=epsilon)], 'observer')

    def test_zero_epsilon_and_exact_positive_rational_neighbors_are_legal(self):
        entries = [self.release(epsilon=0), self.release('release-2', '1/3'), self.release('release-3', Fraction(2, 3))]
        result = visible_privacy_ledger(entries, 'observer')
        self.assertEqual(result['basic_composition_epsilon'], Fraction(1)); self.assertEqual(result['visible_mechanisms'], 3)

    def test_nonfinite_malformed_unknown_or_boolean_parameters_are_rejected(self):
        for epsilon in (True, None, float('nan'), float('inf'), float('-inf'), 'NaN', 'Infinity', '1/0', 'unknown', [], {}):
            with self.subTest(epsilon=repr(epsilon)), self.assertRaises(ContractError):
                visible_privacy_ledger([self.release(epsilon=epsilon)], 'observer')

    def test_adding_nonnegative_release_never_refunds_basic_composition(self):
        entries = []; previous = Fraction(0)
        for index, epsilon in enumerate((0, '1/7', '2/7', Fraction(0), '3/7')):
            entries.append(self.release(str(index), epsilon)); result = visible_privacy_ledger(entries, 'observer')
            self.assertGreaterEqual(result['basic_composition_epsilon'], previous); previous = result['basic_composition_epsilon']

    def test_existing_output_redistribution_without_new_access_is_not_a_new_parameter(self):
        entries = [self.release(epsilon=0), {'id': 'copy', 'visible_to': ['observer'], 'same_preexisting_release': 'release-1', 'new_private_access': False}]
        result = visible_privacy_ledger(entries, 'observer')
        self.assertEqual(result['basic_composition_epsilon'], 0); self.assertEqual(result['visible_mechanisms'], 1)
        entries[1]['new_private_access'] = True
        with self.assertRaises(ContractError): visible_privacy_ledger(entries, 'observer')

    def test_trusted_internal_state_requires_the_declared_proof_boundary(self):
        internal = {'id': 'internal-selection', 'visible_to': [], 'influences_visible_result': True, 'covered_by_mechanism_proof': True}
        result = visible_privacy_ledger([internal, self.release()], 'observer')
        self.assertEqual(result['assumption_gaps'], []); self.assertEqual(result['basic_composition_epsilon'], Fraction(1, 2))
        internal['covered_by_mechanism_proof'] = False
        self.assertEqual(visible_privacy_ledger([internal], 'observer')['assumption_gaps'], ['internal-selection'])

class AdmissionStateTests(unittest.TestCase):
    def check(self, state, allowed, use, expected=None, actual=None):
        return check_admission({'weights': 'W', 'tokenizer': 'T'} if expected is None else expected,
                               {'weights': 'W', 'tokenizer': 'T'} if actual is None else actual, state, allowed, use)

    def test_unknown_and_unexecuted_states_do_not_admit_training(self):
        for state in ('unrecognized-state', 'unknown', 'not-run', 'pending', 'rejected', 'withdrawn', '', None, True):
            with self.subTest(state=state), self.assertRaises(ContractError): self.check(state, ['train'], 'train')

    def test_static_inspection_cannot_be_promoted_to_training_or_publication(self):
        for use in ('train', 'evaluate', 'publish'):
            with self.subTest(use=use), self.assertRaises(ContractError): self.check('limited-static-check', [use], use)

    def test_limited_static_inspection_neighbor_is_legal(self):
        self.assertTrue(self.check('limited-static-check', ['inspect'], 'inspect'))

    def test_limited_research_train_evaluate_and_inspect_neighbors_are_legal(self):
        for use in ('train', 'evaluate', 'inspect'):
            with self.subTest(use=use): self.assertTrue(self.check('limited-research', [use], use))

    def test_research_and_publication_do_not_imply_each_other(self):
        self.assertTrue(self.check('limited-publication', ['publish'], 'publish'))
        for state, use in (('limited-research', 'publish'), ('limited-publication', 'train')):
            with self.subTest(state=state), self.assertRaises(ContractError): self.check(state, [use], use)

    def test_current_use_must_also_be_explicitly_listed(self):
        with self.assertRaises(ContractError): self.check('limited-research', ['inspect'], 'train')

    def test_bad_or_conflicting_use_lists_are_not_authority(self):
        for allowed in ('train', [], ['train', 'train'], [None], ['train', 'unknown-use']):
            with self.subTest(allowed=allowed), self.assertRaises(ContractError): self.check('limited-research', allowed, 'train')
        with self.assertRaises(ContractError): self.check('limited-static-check', ['inspect', 'train'], 'inspect')

    def test_current_bundle_identity_is_still_required(self):
        with self.assertRaises(ContractError): self.check('limited-research', ['train'], 'train', actual={'weights': 'W', 'tokenizer': 'T2'})

class ExactLearningTests(unittest.TestCase):
    def test_weighted_objectives_are_distinct_and_lawful(self):
        self.assertEqual([reduction([2,4],[1,3],p) for p in ('sum','element-mean','weight-mean')],[F(14),F(7),F(7,2)])
    def test_microbatch_element_mean_known_solution(self):self.assertEqual(microbatch_mean([[1,3],[9]]),F(13,3))
    def test_microbatch_group_equal_legal_neighbor(self):self.assertEqual(microbatch_mean([[1,3],[9]],'group-mean'),F(11,2))
    def test_zero_effective_denominator_rejected(self):
        with self.assertRaises(ContractError):reduction([])
    def test_weight_zero_only_invalid_for_weight_denominator(self):
        self.assertEqual(reduction([2,4],[0,0],'sum'),0)
        with self.assertRaises(ContractError):reduction([2,4],[0,0],'weight-mean')
    def test_quadratic_gradient_and_known_update(self):
        self.assertEqual(derivative(0),-6);self.assertEqual(sgd(0,derivative(0),F(1,2)),3)
    def test_derivative_sign_error_is_observable(self):self.assertNotEqual(sgd(0,-derivative(0),F(1,2)),3)
    def test_momentum_reference_and_resumed_known_solution(self):
        a=momentum_step(MomentumState());b=momentum_step(a);c=momentum_step(b)
        self.assertEqual((a.w,b.w,c.w),(F(3,2),F(3),F(15,4)))
        self.assertEqual(momentum_step(MomentumState(b.w,b.velocity,b.accepted)),c)
    def test_missing_momentum_changes_resumed_trajectory(self):
        b=momentum_step(momentum_step(MomentumState()))
        lost=momentum_step(MomentumState(b.w,F(0),b.accepted))
        self.assertEqual(lost.w,3);self.assertNotEqual(lost.w,F(15,4))
    def test_fixed_hypothesis_bound_not_data_selected_bound(self):
        r=selection_failure_rates();self.assertEqual(r['each_fixed_failure'],F(1,2));self.assertEqual(r['data_selected_failure'],1)
    def test_equal_observational_distributions_do_not_identify_causal_effect(self):
        r=causal_nonidentification();self.assertEqual(r['observational_support']['A'],r['observational_support']['B'])
        self.assertEqual(r['causal_mean_difference'],{'A':F(1),'B':F(0)})
    def test_declared_structural_assumption_can_legitimately_distinguish_models(self):
        r=causal_nonidentification();self.assertEqual(r['do0_do1_means']['A'],(0,1));self.assertEqual(r['do0_do1_means']['B'],(F(1,2),F(1,2)))
    def test_exact_central_difference(self):self.assertEqual(central_difference(quadratic,F(7,3),F(1,100)),derivative(F(7,3)))
    def test_legal_optimum_zero_gradient(self):self.assertEqual(derivative(3),0);self.assertEqual(sgd(3,0,F(1,2)),3)
    def test_constrained_boundary_need_not_zero_gradient(self):
        fn=lambda x:(x+1)**2
        self.assertEqual(central_difference(fn,F(0),F(1,10)),2)
        self.assertLess(fn(F(0)),fn(F(1,10)))
    def test_clipping_direction_and_norm(self):
        x,y=clip_3_4(2);self.assertEqual((x,y),(F(6,5),F(8,5)));self.assertEqual(x*x+y*y,4)
    def test_unscaled_clip_not_scaled_threshold(self):
        self.assertNotEqual(tuple(x/8 for x in clip_3_4(2)),clip_3_4(2))
    def test_scale_constant_accumulation(self):
        w=ScaleWindow();w.add(2,8);w.add(3,8);self.assertEqual(w.unscale(),5)
    def test_scale_change_rejected(self):
        w=ScaleWindow();w.add(2,8)
        with self.assertRaises(ContractError):w.add(3,16)
    def test_unscale_twice_rejected(self):
        w=ScaleWindow();w.add(2,8);w.unscale()
        with self.assertRaises(ContractError):w.unscale()
    def test_rejected_update_clocks_are_distinct(self):
        c=Clock().advance(True,4).advance(False,3)
        self.assertEqual((c.attempts,c.accepted,c.tokens),(2,1,7));self.assertEqual(c.schedule_tick('accepted'),1);self.assertEqual(c.schedule_tick('tokens'),7)
    def test_nonfinite_arithmetic_input_rejected(self):
        with self.assertRaises(ContractError):reduction([float('nan')])
    def test_finite_domain_not_all_reals(self):
        p=finite_proof_results();self.assertTrue(p['all_x_squared_ge_x']);self.assertEqual(p['real_counterexample'],F(-1,4))
    def test_expectation_not_pathwise(self):
        p=finite_proof_results();self.assertEqual(p['expectation'],1);self.assertGreater(p['rare_path_value'],1)
    def test_big_o_not_small_finite_value(self):self.assertEqual(finite_proof_results()['asymptotic_example_n100'],10000)

class DataStatisticsTests(unittest.TestCase):
    def setUp(self):self.data=json.loads((ROOT/'examples/model-research-record-fixture.json').read_text())
    def test_failed_and_unknown_runs_not_erased(self):
        r=ledger(self.data['runs']);self.assertEqual(r['planned'],4);self.assertEqual(r['counts']['failure'],1);self.assertEqual(r['counts']['pending'],1);self.assertEqual(r['success_conditional_mean'],F(9,10))
    def test_conditional_mean_not_overall_score(self):
        r=ledger(self.data['runs']);self.assertNotEqual(r['success_conditional_mean'],F(9,20));self.assertEqual(r['terminal_denominator'],3)
    def test_duplicate_run_identity_rejected(self):
        with self.assertRaises(ContractError):ledger(self.data['runs']+[self.data['runs'][0]])
    def test_paired_resampling_keeps_constant_difference(self):
        d=resampled_differences([0,10,20],[1,11,21]);self.assertEqual(len(d),27);self.assertEqual(set(d),{F(1)});self.assertEqual(population_variance(d),0)
    def test_unpaired_resampling_changes_difference_uncertainty(self):
        d=resampled_differences([0,10,20],[1,11,21],False);self.assertEqual(len(d),729);self.assertGreater(population_variance(d),0)
    def test_same_subject_future_legal(self):self.assertEqual(check_split(self.data['split'],'same-subject-future',10),'same-subject-future')
    def test_same_subject_not_cross_subject_generalization(self):
        with self.assertRaises(ContractError):check_split(self.data['split'],'cross-subject')
    def test_cross_subject_isolated_legal(self):
        data=copy.deepcopy(self.data['split']);data[1]['group']='other-subject';self.assertEqual(check_split(data,'cross-subject'),'cross-subject')
    def test_backfilled_training_information_rejected(self):
        data=copy.deepcopy(self.data['split']);data[0]['label_available_at']=11
        with self.assertRaises(ContractError):check_split(data,'same-subject-future',10)
    def test_feature_not_available_at_prediction_rejected(self):
        data=copy.deepcopy(self.data['split']);data[1]['available_at']=14
        with self.assertRaises(ContractError):check_split(data,'same-subject-future',10)
    def test_heldout_fitting_breaks_independent_claim(self):
        data=copy.deepcopy(self.data['split']);data[1]['group']='other'
        with self.assertRaises(ContractError):check_split(data,'cross-subject',fit_roles=('train','test-unlabeled'))
    def test_declared_transductive_neighbor_allowed_with_narrowed_claim(self):self.assertEqual(check_split(self.data['split'],'transductive',fit_roles=('train','test-unlabeled')),'transductive-not-independent-test')
    def test_transductive_test_labels_still_rejected(self):
        with self.assertRaises(ContractError):check_split(self.data['split'],'transductive',fit_roles=('train','test-labels'))
    def test_same_seed_not_full_rng_position(self):
        a=random.Random(17);b=random.Random(17);b.random();self.assertNotEqual(a.getstate(),b.getstate())
        a.setstate(b.getstate());self.assertEqual(a.random(),b.random())

class ParallelRecoveryTests(unittest.TestCase):
    def test_dp_not_world_size(self):self.assertEqual(topology(2,2,2),{'world_size':8,'data_replicas':2})
    def test_sampler_padding_is_not_new_independent_sample(self):
        xs=sampler_indices(5,2,0)+sampler_indices(5,2,1);self.assertEqual(len(xs),6);self.assertEqual(len(set(xs)),5);self.assertEqual(Counter(xs)[0],2)
    def test_declared_drop_tail_has_honest_coverage(self):self.assertEqual(sampler_indices(5,2,0,True)+sampler_indices(5,2,1,True),[0,2,1,3])
    def test_tensor_partial_outputs_need_assembly(self):
        whole=matvec([[1,2],[3,4]],[5,6]);left=matvec([[1],[3]],[5]);right=matvec([[2],[4]],[6]);self.assertEqual(tuple(x+y for x,y in zip(left,right)),whole);self.assertNotEqual(left,whole)
    def test_shard_coverage_and_reshard_by_logical_position(self):
        self.assertEqual(check_shards(4,[{'start':2,'values':[3,4]},{'start':0,'values':[1,2]}]),(1,2,3,4))
    def test_missing_and_overlapping_shards_rejected(self):
        for xs in ([{'start':0,'values':[1,2]}],[{'start':0,'values':[1,2]},{'start':1,'values':[2,3,4]}]):
            with self.assertRaises(ContractError):check_shards(4,xs)
    def test_declared_replicas_legal(self):self.assertEqual(check_shards(2,[{'start':0,'values':[1,2]},{'start':0,'values':[1,2],'replica':True}]),(1,2))
    def test_collective_order_and_root_mismatch(self):
        for ev in (event('broadcast'),event(root=1),event(group='other')):
            with self.assertRaises(ContractError):check_collectives({0:[event()],1:[ev]})
    def test_supported_uneven_gather_neighbor(self):self.assertTrue(check_collectives({0:[event('all-gather',shape=(2,))],1:[event('all-gather',shape=(3,))]},allow_uneven=True))
    def test_async_dependency_required(self):
        with self.assertRaises(ContractError):dependent_buffer_use(False,False)
        self.assertTrue(dependent_buffer_use(False,True))
    def test_complete_same_cut_snapshot(self):self.assertTrue(snapshot_check(snapshot(),REQUIRED))
    def test_mixed_cut_rejected(self):
        s=snapshot();s['components']['momentum']['cut']=8
        with self.assertRaises(ContractError):snapshot_check(s,REQUIRED)
    def test_missing_required_history_rejected(self):
        s=snapshot();s['components'].pop('momentum')
        with self.assertRaises(ContractError):snapshot_check(s,REQUIRED)
    def test_duplicate_consumed_or_accepted_id_rejected(self):
        for key in ('accepted','consumed'):
            s=snapshot();s['components']['contribution_ledger']['value'][key].append(1)
            with self.assertRaises(ContractError):snapshot_check(s,REQUIRED)
    def test_accepted_clock_must_match_modeled_one_item_attempts(self):
        s=snapshot();s['components']['schedule']['value']['accepted']=7
        with self.assertRaises(ContractError):snapshot_check(s,REQUIRED)
    def test_no_history_fullbatch_needs_no_fictional_slots(self):
        s=snapshot();s['components']={'parameters':s['components']['parameters']};self.assertTrue(snapshot_check(s,('parameters',)))
    def test_staging_without_upload_not_published(self):
        s=snapshot();s['uploaded']=False
        with self.assertRaises(ContractError):Publisher().publish(s,REQUIRED,1,0)
    def test_stale_writer_and_cas_conflict_rejected(self):
        p=Publisher(epoch=2)
        with self.assertRaises(ContractError):p.publish(snapshot(),REQUIRED,1,0)
        self.assertEqual(p.publish(snapshot(),REQUIRED,2,0),'snapshot-cut7')
        with self.assertRaises(ContractError):p.publish(snapshot(),REQUIRED,2,0)
    def test_consumed_rejected_sample_may_resume_next(self):
        s=snapshot();self.assertTrue(snapshot_check(s,REQUIRED));self.assertEqual(s['components']['cursor']['value'],8);self.assertEqual(s['components']['schedule']['value']['accepted'],6)
    def test_prefetched_cursor_cannot_skip_unconsumed(self):
        s=snapshot();s['components']['cursor']['value']=13
        with self.assertRaises(ContractError):snapshot_check(s,REQUIRED)
    def test_unknown_execution_and_known_uncovered_are_independent_axes(self):
        self.assertEqual(replay_decision('unknown','not-covered'),'reconcile-required; no blind retry')
        self.assertIn('original execution fact unchanged',replay_decision('unknown','not-covered',True,True,True))
    def test_rollback_does_not_erase_external_effects(self):self.assertEqual(replay_decision('accepted','not-covered',True,True,False),'reconcile-required; no blind retry')
    def test_current_state_retry_of_unknown_rejected(self):self.assertEqual(replay_decision('unknown','not-covered',False,True,True),'reconcile-required; no blind retry')
    def test_covered_model_state_still_requires_external_reconcile(self):self.assertEqual(replay_decision('accepted','covered'),'model-cut-covered; reconcile external effects')

class MaterialPrivacyLifecycleTests(unittest.TestCase):
    def test_joint_identity_not_weight_only(self):
        with self.assertRaises(ContractError):match_bundle({'weights':'W1','tokenizer':'T1'},{'weights':'W1','tokenizer':'T2'})
    def test_non_tokenizer_model_legal(self):self.assertTrue(match_bundle({'index':'I1','features':'F1'},{'index':'I1','features':'F1'}))
    def test_label_same_shape_not_same_semantics(self):
        with self.assertRaises(ContractError):check_label_mapping(['cat','dog'],['dog','cat'],[0,1])
        self.assertTrue(check_label_mapping(['cat','dog'],['dog','cat'],[1,0]))
    def test_teacher_cache_version_mismatch(self):
        with self.assertRaises(ContractError):check_teacher_cache(('teacher-v1','template-A'),('teacher-v2','template-A'))
    def test_linear_merge_known_algebra(self):self.assertEqual(lora_values(5,2,3,7),(F(77),F(77)))
    def test_factor_sum_is_not_sum_of_updates(self):self.assertEqual((2+4)*(1+3),24);self.assertEqual(2*1+4*3,14);self.assertNotEqual(24,14)
    def test_finite_dp_binary_random_response(self):self.assertTrue(finite_dp_bound(rr_distribution(0),rr_distribution(1)))
    def test_dp_probability_and_bound_preconditions(self):
        with self.assertRaises(ContractError):finite_dp_bound({0:F(1,2)},{0:F(1,2)})
        with self.assertRaises(ContractError):finite_dp_bound({0:F(1)},{0:F(1)},F(1,2))
        with self.assertRaises(ContractError):finite_dp_bound({0:F(-1),1:F(2)},{0:F(1)})
    def test_public_reconstructible_coin_breaks_original_guarantee(self):self.assertFalse(finite_dp_bound(rr_distribution(0,True),rr_distribution(1,True)))
    def test_visible_candidates_count_not_only_published_winner(self):
        xs=[{'id':'failed-candidate','visible_to':['analyst'],'epsilon':'1/2','unit':'event'},{'id':'winner','visible_to':['analyst'],'epsilon':'1/2','unit':'event'}]
        r=visible_privacy_ledger(xs,'analyst');self.assertEqual(r['visible_mechanisms'],2);self.assertEqual(r['basic_composition_epsilon'],1)
    def test_preexisting_dp_output_redistribution_neighbor(self):
        xs=[{'id':'r1','visible_to':['a'],'epsilon':1,'unit':'record'},{'id':'copy','visible_to':['a'],'same_preexisting_release':'r1','new_private_access':False}]
        self.assertEqual(visible_privacy_ledger(xs,'a')['basic_composition_epsilon'],1)
    def test_new_private_access_not_free_postprocessing(self):
        xs=[{'id':'r1','visible_to':['a'],'epsilon':1,'unit':'record'},{'id':'copy','visible_to':['a'],'same_preexisting_release':'r1','new_private_access':True}]
        with self.assertRaises(ContractError):visible_privacy_ledger(xs,'a')
    def test_hidden_influencing_state_needs_mechanism_proof(self):
        xs=[{'id':'selection','visible_to':[],'influences_visible_result':True,'covered_by_mechanism_proof':False}]
        self.assertEqual(visible_privacy_ledger(xs,'a')['assumption_gaps'],['selection'])
        xs[0]['covered_by_mechanism_proof']=True;self.assertEqual(visible_privacy_ledger(xs,'a')['assumption_gaps'],[])
    def test_mixed_privacy_units_not_silently_equal(self):
        xs=[{'id':'r1','visible_to':['a'],'epsilon':1,'unit':'event'},{'id':'r2','visible_to':['a'],'epsilon':1,'unit':'user'}]
        with self.assertRaises(ContractError):visible_privacy_ledger(xs,'a')
    def test_withdrawn_cache_rejected(self):
        with self.assertRaises(ContractError):check_admission({'id':'A'},{'id':'A'},'withdrawn',['train'],'train')
    def test_restricted_valid_admission_legal(self):self.assertTrue(check_admission({'id':'A'},{'id':'A'},'limited-research',['train'],'train'))
    def test_pending_not_auto_promoted_by_no_findings(self):
        with self.assertRaises(ContractError):check_admission({'id':'A'},{'id':'A'},'pending',['train'],'train')
    def test_path_escape_rejected_unicode_spaces_legal(self):
        with self.assertRaises(ContractError):manifest_path('../outside')
        self.assertEqual(manifest_path('合成 数据/part 1.json'),'合成 数据/part 1.json')
    def test_settlement_replaces_estimate_not_double_count(self):
        xs=json.loads((ROOT/'examples/model-research-record-fixture.json').read_text())['costs'];r=cost_ledger(xs);self.assertEqual(r['amount_by_currency']['USD'],7);self.assertFalse(r['complete']);self.assertEqual(len(r['unknown_meters']),1)
    def test_conflicting_same_revision_cost_rejected(self):
        x={'target':'g','meter':'m','status':'settled','revision':1,'amount':2,'currency':'USD'};y=dict(x,amount=3)
        with self.assertRaises(ContractError):cost_ledger([x,y])
    def test_original_bytes_not_parsed_text_identity(self):
        with self.assertRaises(ContractError):provenance_identity('parsed-text','original-pdf-bytes')
        self.assertTrue(provenance_identity('parsed-text','parsed-text'))
    def test_disposition_has_no_effect_and_no_forgetting_claim(self):
        p=disposition_plan('checkpoint',True,True,True,'original only');self.assertFalse(p['effects_executed']);self.assertFalse(p['model_forgetting_established']);self.assertTrue(p['reproducibility_loss'])
    def test_read_only_actor_cannot_execute_disposition(self):
        with self.assertRaises(ContractError):disposition_plan('A',True,False,True,'original')
    def test_no_basis_disposition_rejected(self):
        with self.assertRaises(ContractError):disposition_plan('A',False,True,False,'original')
    def test_delivery_complete_billing_pending_legal(self):
        r=delivery_states(True,False,False,False);self.assertEqual(r['artifact_delivery'],'complete');self.assertEqual(r['billing'],'pending');self.assertEqual(r['deployment'],'unverified')

if __name__=="__main__": unittest.main()
