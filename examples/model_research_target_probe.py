"""Target probes with explicit library identities. These are NOT a training harness.

Library/device probes require their declared target environment. Record probes only
check record structure and finite arithmetic, never authenticity, rights or real effects.
"""
import sys
if sys.flags.optimize:raise SystemExit('normal Python mode required; -O/-OO rejected')
from pathlib import Path
import argparse,importlib.metadata,json,math,io,os
from datetime import timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'checks'))
from model_research_finite import (need,ledger,cost_ledger,check_split,finite_dp_bound,rr_distribution,visible_privacy_ledger,disposition_plan,delivery_states)
from fractions import Fraction
from validation_common import read_json

def versions(required):
    observed={}
    for name,expected in required.items():
        actual=importlib.metadata.version(name);observed[name]=actual
        need(actual.split('+',1)[0]==expected,f'{name} version {actual} differs from contract {expected}; establish a new target binding before running')
    return observed

def records(path):
    data=read_json(path)
    need(data['fixture_kind']=='synthetic-research-contract-records','unknown record contract')
    need(all(c.get('id') and c.get('statement') and c.get('proof_or_result_ref') and c.get('support_status') for c in data['claims']),'incomplete claim mapping')
    return {'claim_records':len(data['claims']),'ledger':ledger(data['runs']), 'record_truth':'not certified; actual rights/authority/proof/result require their own evidence'}

def torch_numerics():
    v=versions({'torch':'2.14.0'});import torch
    x=torch.tensor(0.,dtype=torch.float64,requires_grad=True);loss=(x-3)**2;loss.backward()
    need(x.grad.item()==-6.,'quadratic derivative mismatch')
    with torch.no_grad():new=x-0.5*x.grad
    need(new.item()==3.,'quadratic known update mismatch')
    logits=torch.zeros(2,dtype=torch.float64);labels=torch.tensor([0.,1.],dtype=torch.float64);w=torch.tensor([1.,3.],dtype=torch.float64)
    mean=torch.nn.BCEWithLogitsLoss(weight=w,reduction='mean')(logits,labels).item()
    total=torch.nn.BCEWithLogitsLoss(weight=w,reduction='sum')(logits,labels).item()
    need(math.isclose(mean,2*math.log(2),rel_tol=1e-12),'fixed-element denominator mismatch')
    need(math.isclose(total,4*math.log(2),rel_tol=1e-12),'sum reduction mismatch')
    torch.manual_seed(17);state=torch.get_rng_state();a=torch.rand(3);torch.set_rng_state(state);b=torch.rand(3)
    need(torch.equal(a,b),'same-environment state restoration mismatch')
    g=torch.tensor([3.,4.],dtype=torch.float64,requires_grad=True);g.grad=torch.tensor([3.,4.],dtype=torch.float64)
    torch.nn.utils.clip_grad_norm_([g],2.)
    need(torch.allclose(g.grad,torch.tensor([1.2,1.6],dtype=torch.float64),atol=1e-6,rtol=0),'unscaled clipping mismatch')
    return {'versions':v,'device':'cpu','quadratic_gradient':x.grad.item(),'known_new_w':new.item(),'weighted_BCE_fixedN_mean':mean,'weighted_BCE_sum':total,'rng_restore_equal':True,'scope':'CPU operations only; not CUDA AMP or cross-platform bitwise evidence'}

def scipy_statistics():
    v=versions({'scipy':'1.18.0'});import numpy as np
    from scipy.optimize import minimize
    from scipy.stats import bootstrap
    r=minimize(lambda x:float((x[0]-3)**2),[0.],method='BFGS',jac=lambda x:np.array([2*(x[0]-3)]),options={'gtol':1e-10,'maxiter':50})
    need(r.success and abs(r.x[0]-3)<1e-8,'BFGS known solution failed')
    p=minimize(lambda x:float((x[0]+1)**2),[2.],method='Powell',bounds=[(0.,None)],options={'xtol':1e-10,'ftol':1e-10,'maxiter':100})
    need(p.x[0]>=0 and p.x[0]<1e-5,'constrained derivative-free boundary solution failed')
    a=np.array([0.,10.,20.]);b=a+1
    stat=lambda aa,bb,axis=-1:np.mean(bb-aa,axis=axis)
    paired=bootstrap((a,b),stat,paired=True,method='percentile',n_resamples=400,rng=np.random.default_rng(17))
    need(paired.confidence_interval.low==1. and paired.confidence_interval.high==1.,'paired constant difference not preserved')
    return {'versions':v,'BFGS_x':r.x.tolist(),'BFGS_message':str(r.message),'Powell_x':p.x.tolist(),'Powell_message':str(p.message),'paired_empirical_percentile_interval':[paired.confidence_interval.low,paired.confidence_interval.high], 'scope':'fixed examples only; this degenerate empirical interval is NOT a population reliability guarantee or a BCa test'}

def distributed():
    v=versions({'torch':'2.14.0'});import torch
    import torch.distributed as dist
    from torch.utils.data.distributed import DistributedSampler
    dist.init_process_group('gloo',timeout=timedelta(seconds=30))
    rank=dist.get_rank();world=dist.get_world_size();need(world==2,'probe requires exactly 2 CPU workers')
    local=torch.tensor([4.,2.] if rank==0 else [9.,1.],dtype=torch.float64)
    work=dist.all_reduce(local,async_op=True);work.wait()
    need(torch.equal(local,torch.tensor([13.,3.],dtype=torch.float64)),'global numerator/denominator mismatch')
    ids=list(DistributedSampler(list(range(5)),num_replicas=2,rank=rank,shuffle=False,drop_last=False))
    need(ids==([0,2,4] if rank==0 else [1,3,0]),'padding identity mismatch')
    result={'versions':v,'rank':rank,'world_size':world,'global_mean':local[0].item()/local[1].item(),'sample_indices':ids,'scope':'Gloo CPU normal completion only; no NCCL stream, fault recovery, durability or training result'}
    dist.destroy_process_group();return result

def dcp(output):
    v=versions({'torch':'2.14.0'});import torch
    import torch.distributed.checkpoint as cp
    out=Path(output);need(not out.exists(),'target output must be a new path; retain old evidence')
    state={'model':torch.tensor([1.,2.],dtype=torch.float64),'accepted_updates':torch.tensor([6]),'next_consumed_sample':torch.tensor([8])}
    cp.save(state,checkpoint_id=out,no_dist=True)
    loaded={'model':torch.zeros(2,dtype=torch.float64),'accepted_updates':torch.zeros(1,dtype=torch.int64),'next_consumed_sample':torch.zeros(1,dtype=torch.int64)}
    cp.load(loaded,checkpoint_id=out,no_dist=True)
    need(all(torch.equal(state[k],loaded[k]) for k in state),'DCP round-trip mismatch')
    return {'versions':v,'checkpoint_path':str(out),'restored':{k:x.tolist() for k,x in loaded.items()},'scope':'single-process FileSystemWriter normal round trip only; full algorithm state, async staging, cross-rank atomic publication, crashes and storage durability remain separate tests'}

def peft_linear():
    v=versions({'torch':'2.14.0','peft':'0.21.0'});import torch
    from peft import LoraConfig,get_peft_model
    class Tiny(torch.nn.Module):
        def __init__(self):super().__init__();self.proj=torch.nn.Linear(2,2,bias=False)
        def forward(self,x):return self.proj(x)
    base=Tiny().double()
    with torch.no_grad():base.proj.weight.copy_(torch.tensor([[1.,2.],[3.,4.]],dtype=torch.float64))
    wrapped=get_peft_model(base,LoraConfig(r=1,lora_alpha=1,target_modules=['proj'],lora_dropout=0.,bias='none')).double().eval()
    modules=[m for m in wrapped.modules() if hasattr(m,'lora_A') and 'default' in m.lora_A]
    need(len(modules)==1,'unexpected adapted module set');layer=modules[0]
    with torch.no_grad():
        layer.lora_A['default'].weight.copy_(torch.tensor([[1.,2.]],dtype=torch.float64))
        layer.lora_B['default'].weight.copy_(torch.tensor([[3.],[4.]],dtype=torch.float64))
        x=torch.tensor([[2.,5.],[-1.,3.]],dtype=torch.float64);before=wrapped(x)
        merged=wrapped.merge_and_unload();after=merged(x)
    err=(before-after).abs().max().item();need(err<=1e-12,'linear merge output error exceeds declared tolerance')
    return {'versions':v,'max_abs_error':err,'target_module':'proj','base_and_adapter_shape':[2,2,1],'scope':'untrained local linear tensors, fixed coordinates/no dropout; no model download, real quality, quantization, nonlinear or task-arithmetic guarantee'}

def safe_load():
    v=versions({'torch':'2.14.0'});import torch
    buf=io.BytesIO();torch.save({'tensor':torch.tensor([1,2,3])},buf);buf.seek(0)
    globals_=torch.serialization.get_unsafe_globals_in_checkpoint(buf);buf.seek(0)
    loaded=torch.load(buf,weights_only=True)
    need(torch.equal(loaded['tensor'],torch.tensor([1,2,3])),'benign restricted-load mismatch')
    return {'versions':v,'reported_unsafe_globals':globals_,'loaded_keys':sorted(loaded),'scope':'benign in-memory tensor round trip only; not malicious file, DoS, memory-corruption or environment-isolation validation'}

def data_sklearn(path):
    v=versions({'scikit-learn':'1.9.1'});import numpy as np
    from sklearn.preprocessing import StandardScaler
    x=np.array([[0.],[2.]]);held=np.array([[10.]])
    scaler=StandardScaler().fit(x);need(scaler.mean_[0]==1.,'train-only fit mismatch')
    applied=scaler.transform(held);need(applied[0,0]==9.,'same training transform not applied to held-out')
    allfit=StandardScaler().fit(np.concatenate([x,held]));need(allfit.mean_[0]==4.,'leakage contrast fixture changed')
    data=read_json(path);split=check_split(data['split'],claim='same-subject-future',cutoff=10)
    return {'versions':v,'training_mean':1.,'held_out_transformed':applied.tolist(),'all_data_fit_mean':4.,'split_record':split,'scope':'preprocessing example and supplied metadata only; not a right-to-use or absence-of-all-contamination certificate'}

def dp_records(path):
    data=read_json(path);r=visible_privacy_ledger(data['privacy_releases'],'analyst')
    return {'finite_binary_mechanism_ratio3':finite_dp_bound(rr_distribution(0),rr_distribution(1)), 'same_mechanism_revealed_coin_ratio3':finite_dp_bound(rr_distribution(0,True),rr_distribution(1,True)),'privacy_metadata':r,'scope':'finite binary randomized response plus metadata composition; no real DP training or accountant validated'}

def lifecycle_records(path):
    data=read_json(path)
    plan=disposition_plan('synthetic-checkpoint',True,True,True,'original checkpoint only')
    return {'disposition':plan,'states':delivery_states(True,False,False,False),'scope':'disposition plan has no deletion, publication, billing or deployment effect; real authority and terminal receipts must be independently obtained'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('profile',choices=['records','torch-numerics','scipy-statistics','distributed-gloo','dcp','peft-linear','safe-load','data-sklearn','dp-records','ledger','lifecycle-records']);ap.add_argument('--input',default='examples/model-research-record-fixture.json');ap.add_argument('--output-dir');a=ap.parse_args()
    fn={'records':lambda:records(a.input),'torch-numerics':torch_numerics,'scipy-statistics':scipy_statistics,'distributed-gloo':distributed,'dcp':lambda:dcp(a.output_dir) if a.output_dir else (_ for _ in ()).throw(ValueError('dcp requires a new --output-dir')),'peft-linear':peft_linear,'safe-load':safe_load,'data-sklearn':lambda:data_sklearn(a.input),'dp-records':lambda:dp_records(a.input),'ledger':lambda:cost_ledger(read_json(a.input)['costs']),'lifecycle-records':lambda:lifecycle_records(a.input)}[a.profile]
    try:result=fn()
    except (ImportError,importlib.metadata.PackageNotFoundError) as e:print(json.dumps({'status':'not-run','reason':str(e)},ensure_ascii=False));return 3
    except Exception as e:print(json.dumps({'status':'failed-or-precondition-unmet','reason':str(e)},ensure_ascii=False));return 1
    print(json.dumps({'status':'probe-completed','profile':a.profile,'result':result},ensure_ascii=False,indent=2,default=lambda x:str(x) if isinstance(x,Fraction) else str(x)));return 0
if __name__=='__main__':raise SystemExit(main())
