"""Technical content contracts for the adopted model-research standards."""
import sys
if sys.flags.optimize: raise RuntimeError("Validation requires assertions enabled; do not use -O or -OO")
import json
from pathlib import Path
from checks.retained_content import research_baseline as base,research_data_experiments as data,research_optimization_adaptation as opt,research_theory_distributed_risks as theory
from checks.retained_content.profile_integrity import validate_profiles,validate_body_identity
EXPECTED_IDS={base.ID,*data.IDS,opt.OPTIMIZATION_ID,opt.ADAPTATION_ID,*theory.SPECS}
from checks.validate_system import ROOT
def validate(entry,body):
 validate_body_identity(entry,body)
 ident=entry['id']
 assert ident in EXPECTED_IDS
 if ident==base.ID:base.assert_model_research_complete(entry,body)
 elif ident in data.IDS:data.assert_topic_complete(entry,body)
 elif ident in (opt.OPTIMIZATION_ID,opt.ADAPTATION_ID):opt.assert_second_topic_complete(entry,body)
 else:theory.assert_third_topic_complete(entry,body)
def inputs():
 return [(e,(ROOT/e['path']).read_text()) for e in validate_profiles(EXPECTED_IDS)]
if __name__=='__main__':
 for entry,body in inputs():validate(entry,body)
 print('9 research document contracts checked; no research/runtime acceptance inferred')
