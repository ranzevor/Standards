"""Finite, synthetic research-contract models; no framework, data, billing or deletion effects.

Assumptions: immutable in-memory records, sequential sample IDs for the cursor example,
trusted comparison inputs, no actual durable store or concurrent process scheduler.
Predicate success is not an authority/rights certificate or a general theorem checker.
"""
import sys
if sys.flags.optimize:
    raise RuntimeError('model-research validation requires normal Python mode; -O/-OO rejected')
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from fractions import Fraction as F
from itertools import product, combinations
from pathlib import PurePosixPath
import math

class ContractError(ValueError): pass

def need(condition, reason):
    if not condition: raise ContractError(reason)

def fraction(x):
    if isinstance(x,float): need(math.isfinite(x),'non-finite arithmetic input')
    return F(x)

def reduction(losses, weights=None, policy='element-mean'):
    need(bool(losses),'zero effective denominator')
    xs=list(map(fraction,losses));ws=list(map(fraction,weights)) if weights is not None else [F(1)]*len(xs)
    need(len(xs)==len(ws),'weight/element mismatch')
    total=sum((x*w for x,w in zip(xs,ws)),F(0))
    if policy=='sum': return total
    if policy=='element-mean': return total/len(xs)
    need(policy=='weight-mean','unknown reduction contract')
    den=sum(ws,F(0));need(den!=0,'zero weight denominator');return total/den

def microbatch_mean(groups, policy='element-mean'):
    need(bool(groups) and all(groups),'empty modeled microbatch requires an explicit skip contract')
    if policy=='group-mean': return sum((reduction(g) for g in groups),F(0))/len(groups)
    need(policy=='element-mean','unknown microbatch objective')
    return reduction([x for g in groups for x in g])

def quadratic(w): return (fraction(w)-3)**2

def derivative(w): return 2*(fraction(w)-3)

def sgd(w,grad,lr): return fraction(w)-fraction(lr)*fraction(grad)

@dataclass(frozen=True)
class MomentumState:
    w:F=F(0)
    velocity:F=F(0)
    accepted:int=0

def momentum_step(state,beta=F(1,2),lr=F(1,4)):
    velocity=fraction(beta)*state.velocity+derivative(state.w)
    return MomentumState(state.w-fraction(lr)*velocity,velocity,state.accepted+1)

def selection_failure_rates():
    # Two equiprobable observations; each fixed hypothesis fails on one outcome.
    # Choosing the failing hypothesis after seeing that observation fails on both.
    return {'each_fixed_failure':F(1,2),'data_selected_failure':F(1),
            'outcomes':(0,1),'failing_hypothesis_by_observation':(0,1)}

def causal_nonidentification():
    # Both models have U~Bernoulli(1/2), X=U. A sets Y=X; B sets Y=U.
    observed={name:tuple((u,u) for u in (0,1)) for name in ('A','B')}
    means={name:tuple(sum((F(x) if name=='A' else F(u) for u in (0,1)),F(0))/2 for x in (0,1)) for name in ('A','B')}
    return {'observational_support':observed,'do0_do1_means':means,
            'causal_mean_difference':{name:v[1]-v[0] for name,v in means.items()},
            'scope':'Two finite structural models only; neither selected by observational fit alone.'}

def central_difference(fn,x,h):
    x,h=fraction(x),fraction(h);need(h>0,'positive perturbation required');return (fn(x+h)-fn(x-h))/(2*h)

def clip_3_4(threshold):
    threshold=fraction(threshold);need(threshold>=0,'negative norm threshold')
    scale=min(F(1),threshold/5);return (3*scale,4*scale)

@dataclass(frozen=True)
class Clock:
    attempts:int=0
    accepted:int=0
    tokens:int=0
    def advance(self, accepted, tokens):
        need(type(accepted) is bool and type(tokens) is int and tokens>=0,'bad progress event')
        return Clock(self.attempts+1,self.accepted+int(accepted),self.tokens+tokens)
    def schedule_tick(self, clock):
        need(clock in ('attempts','accepted','tokens'),'unknown schedule clock')
        return getattr(self,clock)

class ScaleWindow:
    def __init__(self): self.scale=None;self.value=F(0);self.unscaled=False
    def add(self,unscaled_grad,scale):
        scale=fraction(scale);need(scale>0,'nonpositive scale');need(not self.unscaled,'cannot add after unscale')
        need(self.scale is None or self.scale==scale,'incompatible accumulation scales')
        self.scale=scale;self.value+=fraction(unscaled_grad)*scale
    def unscale(self):
        need(self.scale is not None and not self.unscaled,'unscale once after nonempty accumulation')
        self.unscaled=True;return self.value/self.scale

def finite_proof_results():
    domain=(0,1,2,3)
    return {'domain':domain,'all_x_squared_ge_x':all(x*x>=x for x in domain),
            'real_counterexample':F(1,2)**2-F(1,2),
            'expectation':F(1,100)*100,'rare_path_value':100,
            'asymptotic_example_n100':F(10**6,100),
            'for_each_integer_successor_rule':'for any integer x, y=x+1; reverse quantifier refuted by x=y'}

def ledger(records):
    states={'success','failure','pending','not-run','invalid'}
    ids=[r['id'] for r in records];need(len(ids)==len(set(ids)),'attempt identity overwritten')
    need(all(r['state'] in states for r in records),'unknown ledger state')
    counts=Counter(r['state'] for r in records)
    scores=[fraction(r['score']) for r in records if r['state']=='success']
    return {'planned':len(records),'counts':dict(counts),'success_conditional_mean':sum(scores,F(0))/len(scores) if scores else None,
            'score_population':'successful runs only; not an end-to-end success-rate estimate',
            'terminal_denominator':counts['success']+counts['failure']+counts['invalid']}

def resampled_differences(a,b,paired=True):
    need(len(a)==len(b) and 0<len(a)<=4,'finite example supports 1..4 paired observations')
    n=len(a);indices=list(product(range(n),repeat=n));out=[]
    if paired:
        for ix in indices: out.append(sum((fraction(b[i])-fraction(a[i]) for i in ix),F(0))/n)
    else:
        for ia in indices:
            for ib in indices:out.append(sum((fraction(b[j])-fraction(a[i]) for i,j in zip(ia,ib)),F(0))/n)
    return out

def population_variance(xs):
    need(bool(xs),'empty distribution');m=sum(xs,F(0))/len(xs);return sum(((x-m)**2 for x in xs),F(0))/len(xs)

def check_split(records,claim='cross-subject',cutoff=None,fit_roles=('train',)):
    need(claim in ('cross-subject','same-subject-future','transductive'),'unsupported split claim')
    need(type(records)is list and all(type(r)is dict and r.get('role')in('train','test') for r in records),'explicit train/test records required')
    train={r['group'] for r in records if r['role']=='train'};test={r['group'] for r in records if r['role']=='test'}
    need(bool(train) and bool(test),'this split claim requires both training and evaluation records')
    if claim=='cross-subject':need(not train & test,'subject-family leakage')
    if claim!='transductive':need(set(fit_roles)<={'train'},'held-out information used for fitting')
    else:need(set(fit_roles)<={'train','test-unlabeled'},'test-label feedback')
    if claim=='same-subject-future':
        need(cutoff is not None,'future prediction requires a training information cutoff')
        def time(value):
            need(type(value)in(int,float,F),'finite numeric temporal coordinate required')
            return fraction(value)
        cutoff=time(cutoff)
        for r in records:
            if r['role']=='train':need(max(time(r['event_at']),time(r['available_at']),time(r.get('label_available_at',r['available_at'])))<=cutoff,'future training information')
            if r['role']=='test':
                prediction=time(r['prediction_at'])
                need(cutoff<=prediction,'training cutoff after evaluation prediction')
                need(time(r['available_at'])<=prediction,'feature unavailable at prediction')
                if 'target_at'in r:need(prediction<=time(r['target_at']),'future target precedes prediction')
    return 'transductive-not-independent-test' if claim=='transductive' else claim

def sampler_indices(n,replicas,rank,drop_last=False):
    need(n>0 and replicas>0 and 0<=rank<replicas,'bad sampler dimensions')
    ids=list(range(n))
    if drop_last:ids=ids[:(n//replicas)*replicas]
    else:
        total=((n+replicas-1)//replicas)*replicas
        ids=(ids*((total+n-1)//n))[:total]
    return ids[rank::replicas]

def topology(dp,tp,pp):
    need(min(dp,tp,pp)>0,'empty topology');return {'world_size':dp*tp*pp,'data_replicas':dp}

def matvec(matrix,vector):
    need(bool(matrix) and all(len(row)==len(vector) for row in matrix),'shape mismatch')
    return tuple(sum((fraction(x)*fraction(y) for x,y in zip(row,vector)),F(0)) for row in matrix)

def check_shards(total,shards):
    cells={};replicas=[]
    for sh in shards:
        need(sh['start']>=0 and sh['start']+len(sh['values'])<=total,'shard outside logical object')
        if sh.get('replica'): replicas.append(sh);continue
        for i,v in enumerate(sh['values'],sh['start']):need(i not in cells,'overlapping logical ownership');cells[i]=v
    need(set(cells)==set(range(total)),'missing logical shard coverage')
    for sh in replicas:
        need(all(cells[i]==v for i,v in enumerate(sh['values'],sh['start'])),'replica not equal to authoritative logical values')
    return tuple(cells[i] for i in range(total))

def check_collectives(traces,allow_uneven=False):
    need(bool(traces),'no participating ranks');first=None
    for events in traces.values():
        sig=[]
        for e in events:
            sig.append(tuple(e[k] for k in ('generation','group','sequence','operation','root'))+(() if allow_uneven and e['operation']=='all-gather' else (tuple(e['shape']),)))
        if first is None:first=sig
        else:need(sig==first,'collective operation/order/group/root/layout mismatch')
    return True

def dependent_buffer_use(completed,dependency_established):
    need(completed or dependency_established,'buffer/result used before required completion dependency');return True

def snapshot_check(snapshot,required):
    need(snapshot['complete'] and snapshot['uploaded'],'snapshot has not completed required save/upload')
    need(set(required)<=set(snapshot['components']),'missing necessary algorithm state')
    need(all(snapshot['components'][name]['cut']==snapshot['cut'] for name in required),'mixed state cuts')
    if 'cursor' in required or 'contribution_ledger' in required:
        need({'cursor','contribution_ledger'}<=set(snapshot['components']),'incomplete required sequential cursor/ledger pair')
        cur=snapshot['components']['cursor']['value'];need(type(cur) is int and cur>=1,'invalid sequential cursor');log=snapshot['components']['contribution_ledger']['value']
        need(all(len(log[k])==len(set(log[k])) for k in ('accepted','rejected','consumed')),'duplicate attempt/contribution identities')
        accepted=set(log['accepted']);rejected=set(log['rejected']);consumed=set(log['consumed'])
        need(not accepted & rejected,'same attempt both accepted and rejected')
        need(accepted|rejected==consumed,'consumption/acceptance ledger not complete')
        need(consumed==set(range(1,cur)),'sequential finite cursor not matched to complete processed cut')
        if 'schedule' in required and 'accepted' in snapshot['components']['schedule']['value']:
            need(snapshot['components']['schedule']['value']['accepted']==len(accepted),'one-sample-per-attempt finite accepted clock mismatch')
    return True

class Publisher:
    def __init__(self,epoch=1):self.epoch=epoch;self.version=0;self.pointer=None
    def publish(self,snapshot,required,writer_epoch,expected_version):
        snapshot_check(snapshot,required)
        need(writer_epoch==self.epoch,'stale writer fence')
        need(expected_version==self.version,'publication compare-and-set conflict')
        self.pointer=snapshot['id'];self.version+=1;return self.pointer

def replay_decision(execution,coverage,at_trusted_snapshot=False,old_writer_fenced=False,external_effects_reconciled=False):
    need(execution in ('not-executed','accepted','rejected','partial','unknown'),'bad execution fact')
    need(coverage in ('covered','not-covered','inconsistent','unknown'),'bad coverage fact')
    if coverage=='covered':return 'continue-after-covered-cut' if external_effects_reconciled else 'model-cut-covered; reconcile external effects'
    if execution=='not-executed' and coverage=='not-covered' and old_writer_fenced and external_effects_reconciled:return 'retry-verified-unapplied'
    if coverage=='not-covered' and at_trusted_snapshot and old_writer_fenced and external_effects_reconciled:return 'replay-after-full-rollback; original execution fact unchanged'
    return 'reconcile-required; no blind retry'

def match_bundle(expected,actual):
    need(expected==actual,'joint bundle identity/interpretation mismatch');return True

def check_label_mapping(teacher,student,mapping):
    need(len(mapping)==len(teacher),'label mapping incomplete')
    need(all(0<=j<len(student) and teacher[i]==student[j] for i,j in enumerate(mapping)),'label dimension not semantic alignment');return True

def check_teacher_cache(requested,generated):
    need(requested==generated,'cache was generated by a different teacher/template/decoder revision');return True

def lora_values(w,a,b,x,scale=1):
    w,a,b,x,scale=map(fraction,(w,a,b,x,scale))
    return ((w+scale*b*a)*x,w*x+scale*b*(a*x))

def rr_distribution(bit,reveal_coin=False):
    need(bit in (0,1),'binary finite mechanism only');d=defaultdict(F)
    for coin in range(4):
        y=bit if coin<3 else 1-bit;obs=(y,coin) if reveal_coin else y;d[obs]+=F(1,4)
    return dict(d)

def finite_dp_bound(distribution0,distribution1,exp_epsilon=F(3)):
    # All singleton inequalities imply all subset inequalities in this finite pure-DP model.
    keys=set(distribution0)|set(distribution1)
    need(bool(keys) and exp_epsilon>=1,'invalid finite pure-DP likelihood-ratio bound')
    for d in (distribution0,distribution1):
        need(all(fraction(p)>=0 for p in d.values()) and sum(map(fraction,d.values()),F(0))==1,'not a probability distribution')
    return all(distribution0.get(k,F(0))<=exp_epsilon*distribution1.get(k,F(0)) and distribution1.get(k,F(0))<=exp_epsilon*distribution0.get(k,F(0)) for k in keys)

def visible_privacy_ledger(entries,observer):
    releases={};epsilons={};pending=[]
    for e in entries:
        if observer not in e['visible_to']:
            if e.get('influences_visible_result') and not e.get('covered_by_mechanism_proof'):pending.append(e['id'])
            continue
        if e.get('same_preexisting_release'):
            need(not e.get('new_private_access'),'new private access is not mere redistribution')
            need(e['same_preexisting_release'] in releases,'unknown preexisting release reference');continue
        need(e['id'] not in releases,'duplicate mechanism identity requires explicit redistribution relation')
        value=e.get('epsilon')
        need(type(value)in(int,float,str,F),'finite nonnegative epsilon required')
        try:epsilon=fraction(value)
        except (ValueError,TypeError,ZeroDivisionError,OverflowError)as exc:
            raise ContractError('malformed or nonfinite epsilon')from exc
        need(epsilon>=0,'negative epsilon cannot refund a release')
        epsilons[e['id']]=epsilon
        releases[e['id']]=e
    units={e['unit'] for e in releases.values()};need(len(units)<=1,'privacy units cannot be silently combined')
    return {'visible_mechanisms':len(releases),'basic_composition_epsilon':sum(epsilons.values(),F(0)),
            'assumption_gaps':pending,'scope':'metadata/basic composition only; not validation of a real DP mechanism/accountant'}

def check_admission(expected_bundle,actual_bundle,state,permitted_use,current_use):
    match_bundle(expected_bundle,actual_bundle)
    # A finite vocabulary, not an authority to grant real material rights.
    allowed={'limited-static-check':{'inspect'},'limited-research':{'inspect','train','evaluate'},
             'limited-publication':{'inspect','publish'}}
    need(type(state)is str and state in allowed,'unknown or inactive admission state')
    need(type(permitted_use)is list and bool(permitted_use)and all(type(x)is str for x in permitted_use),'explicit permitted use list required')
    need(len(permitted_use)==len(set(permitted_use))and set(permitted_use)<=allowed[state],'admission state does not permit declared use')
    need(type(current_use)is str and current_use in allowed[state],'admission state does not permit current use')
    need(current_use in permitted_use,'use not covered by admission record');return True

def manifest_path(path):
    p=PurePosixPath(path)
    need(bool(path) and not p.is_absolute() and '..' not in p.parts and '\\' not in path and '\0' not in path,'manifest path outside payload or invalid')
    return str(p)

def cost_ledger(entries):
    bykey=defaultdict(list)
    for e in entries:bykey[(e['target'],e['meter'])].append(e)
    sums=defaultdict(F);unknown=[]
    for key,rows in bykey.items():
        settled=[e for e in rows if e['status']=='settled'];known=settled or [e for e in rows if e['status']=='estimate']
        if not known:unknown.append(key);continue
        top=max(e['revision'] for e in known);chosen=[e for e in known if e['revision']==top]
        need(len({(e['currency'],str(e['amount'])) for e in chosen})==1,'conflicting same-revision cost authority')
        e=chosen[0];sums[e['currency']]+=fraction(e['amount'])
    return {'amount_by_currency':dict(sums),'unknown_meters':unknown,'complete':not unknown,'meter_count':len(bykey)}

def provenance_identity(actual_kind,declared_kind):
    need(actual_kind==declared_kind,'parsed/OCR text cannot be labelled original bytes identity');return True

def disposition_plan(object_id,covered_basis,actor_has_execution_right,current_reference,requested_scope):
    need(covered_basis,'no valid disposition basis')
    need(actor_has_execution_right,'read-only actor cannot execute disposition')
    return {'object':object_id,'scope':requested_scope,'plan_only':True,'effects_executed':False,
            'reproducibility_loss':bool(current_reference),'model_forgetting_established':False}

def delivery_states(artifact_received,billing_final,channel_identity_verified,deployed_identity_verified):
    return {'artifact_delivery':'complete' if artifact_received else 'pending','billing':'settled' if billing_final else 'pending',
            'channel_publication':'verified' if channel_identity_verified else 'unverified','deployment':'verified' if deployed_identity_verified else 'unverified'}
