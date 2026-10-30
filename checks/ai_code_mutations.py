"""Run actual mutants in isolated temporary copies, retain every raw result."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pathlib,subprocess,tempfile,shutil,json,datetime,hashlib,time,re
BASE=pathlib.Path(__file__).resolve().parents[1]
variants=[
('CM-legacy-resulttype',"rt=result.get('resultType','complete')","rt=result.get('resultType','unsupported')"),
('CM-whole-directory-reject','return valid,rejected','return ([] if rejected else valid),rejected'),
('CM-old-epoch-overwrite','if(e.task,e.attempt,e.epoch,e.plan)!=(self.task,self.attempt,self.epoch,self.plan):', 'if(e.task,e.attempt,e.plan)!=(self.task,self.attempt,self.plan):'),
('CM-unknown-budget-release',"if e.status=='reserved':e.status='unknown'","if e.status=='reserved':e.status='released'"),
('CM-deletion-generation-reset',"self.tombstones[k]=max(self.tombstones.get(k,0),m.version if m else 0)+1",'self.tombstones[k]=0'),
('CM-claim-stays-fresh',"r['status']='stale';changed.append(k);queue.append(('claim:'+k,'stale'))","r['status']='fresh';changed.append(k);queue.append(('claim:'+k,'stale'))"),
('CM-archive-traversal',"p.is_absolute()or'..'in p.parts or", "p.is_absolute()or False or"),
('CM-memory-stale-restore', 'if old is not None and m.version<old.version:', 'if False:'),
('CM-memory-conflicting-version', 'if canonical(asdict(m))!=canonical(asdict(old)):', 'if False:'),
('CM-memory-put-version', 'if old is not None and m.version<=old.version:', 'if False:'),
('CM-memory-deleted-recreation', 'if old is None and k in self.tombstones:', 'if False:'),
('CM-current-root-budget-rollback', "budget=Budget.reconcile(prior['budget'],latest['budget'])", "budget=Budget.restore(prior['budget'])"),
('CM-failed-to-success', "if self.status in('cancelled','failed'):raise ValueError('terminal guard')", "if self.status=='cancelled':raise ValueError('terminal guard')"),
('CM-current-terminal-rollback', "c.status=latest['status']", "c.status=prior['status']"),
('CM-current-plan-rollback', "c.plan=latest['plan']", "c.plan=prior['plan']"),
('CM-current-uncertainty-forgotten', "if prior.status=='unknown' and latest.status=='reserved':", 'if False:')]
def run(evidence_dir=None):
    output=pathlib.Path(evidence_dir) if evidence_dir is not None else pathlib.Path(tempfile.gettempdir())/'StandardsAIMutations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if output.resolve().is_relative_to(BASE.resolve()):raise ValueError('mutation evidence must be outside the reviewed source tree')
    output.mkdir(parents=True,exist_ok=True)
    source=(BASE/'checks/ai_agent_model.py').read_text()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');evidence=output/('code-mutations-'+stamp);evidence.mkdir(parents=True);rows=[]
    with tempfile.TemporaryDirectory(prefix='ai-agent-mutants-')as temp:
        root=pathlib.Path(temp);(root/'checks').mkdir();(root/'checks/__init__.py').write_text('');(root/'tests/ai_agent').mkdir(parents=True)
        shutil.copy2(BASE/'checks/ai_evidence_gate.py',root/'checks/ai_evidence_gate.py')
        for name in ('test_ai_agent_model.py','test_ai_restoration.py'):
            shutil.copy2(BASE/'tests/ai_agent'/name,root/'tests/ai_agent'/name)
        for key,before,after in variants+[('CM-LEGAL-whitespace','def integer(value, minimum=0):','def integer(value, minimum = 0):')]:
            count=source.count(before)
            if count!=1:raise ValueError((key,'mutation not unique',count))
            mutant=source.replace(before,after,1);(root/'checks/ai_agent_model.py').write_text(mutant);shutil.rmtree(root/'checks/__pycache__',ignore_errors=True)
            start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic();command=[sys.executable,'-B','-m','unittest','discover','-s','tests/ai_agent','-v'];r=subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);duration=time.monotonic()-t
            raw=evidence/(key+'.raw.log');raw.write_bytes(r.stdout);legal='LEGAL'in key;actual='accepted'if r.returncode==0 else'killed'
            rows.append({'id':key,'scope':'finite-reference-model','source_sha256':hashlib.sha256(source.encode()).hexdigest(),'mutant_sha256':hashlib.sha256(mutant.encode()).hexdigest(),'before':before,'after':after,'command':command,'started_at_utc':start,'duration_seconds':duration,'exit_code':r.returncode,'expected':'accepted'if legal else'killed','actual':actual,'raw_log':str(raw),'raw_sha256':hashlib.sha256(r.stdout).hexdigest(),'tests_executed':int(re.search(rb'Ran (\d+) tests?',r.stdout).group(1))})
            if (r.returncode==0)!=legal:raise AssertionError(rows[-1])
    (evidence/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'code_mutants_killed':len(variants),'legal_code_neighbor_accepted':1,'raw_model_tests_per_variant':rows[0]['tests_executed'],'report':str(evidence/'results.json')}))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--evidence-dir',type=pathlib.Path);args=parser.parse_args();run(args.evidence_dir)
