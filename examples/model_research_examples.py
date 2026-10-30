"""Run small known-solution examples; only Python standard library is required."""
import sys
if sys.flags.optimize:raise SystemExit('normal Python mode required; -O/-OO rejected')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'checks'))
import argparse,json
from fractions import Fraction as F
from model_research_finite import *

def stringify(x):
    if isinstance(x,F):return str(x)
    raise TypeError(type(x).__name__)

def examples():
    paired=resampled_differences([0,10,20],[1,11,21],True)
    unpaired=resampled_differences([0,10,20],[1,11,21],False)
    c=Clock().advance(True,4).advance(False,3)
    m1=momentum_step(MomentumState());m2=momentum_step(m1);m3=momentum_step(m2)
    lost_history=momentum_step(MomentumState(m2.w,F(0),m2.accepted))
    return {'known_solutions':{
      'weighted_sum':reduction([2,4],[1,3],'sum'),
      'weighted_fixed_N_mean':reduction([2,4],[1,3],'element-mean'),
      'weight_normalized_mean':reduction([2,4],[1,3],'weight-mean'),
      'element_mean_unequal_microbatches':microbatch_mean([[1,3],[9]]),
      'group_equal_mean':microbatch_mean([[1,3],[9]],'group-mean'),
      'quadratic_one_step_w':sgd(0,derivative(0),F(1,2)),
      'clipped_3_4':clip_3_4(2),'attempts_accepted_tokens':(c.attempts,c.accepted,c.tokens),
      'paired_empirical_resample_variance':population_variance(paired),
      'unpaired_empirical_resample_variance':population_variance(unpaired),
      'momentum_reference_w':(m1.w,m2.w,m3.w),
      'momentum_restored_final_w':momentum_step(m2).w,
      'momentum_history_lost_final_w':lost_history.w,
      'selection_failure_rates':selection_failure_rates(),
      'two_model_causal_nonidentification':causal_nonidentification(),
      'finite_proof':finite_proof_results(),'DPxTPxPP':topology(2,2,2),
      'sampler_padded':[sampler_indices(5,2,r) for r in range(2)],
      'linear_LoRA_two_forms':lora_values(5,2,3,7),
      'factor_sum_cross_terms':(F((2+4)*(1+3)),F(2*1+4*3)),
      'finite_binary_rr_DP_ratio_3':finite_dp_bound(rr_distribution(0),rr_distribution(1)),
      'revealed_coin_DP_ratio_3':finite_dp_bound(rr_distribution(0,True),rr_distribution(1,True)),
      'unknown_execution_old_cut':replay_decision('unknown','not-covered',True,True,True)
    },'scope':'Exact synthetic arithmetic/finite states. Pairing variance is conditional on these empirical observations, not a population confidence guarantee. Binary randomized-response enumeration is only that finite mechanism. No real training, backend durability, data rights, billing or deletion is established.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--json',action='store_true');ap.parse_args()
    print(json.dumps(examples(),ensure_ascii=False,indent=2,default=stringify))
