"""Real Terraform Core checks on isolated built-in state, never cloud resources."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,subprocess,sys,argparse
if sys.flags.optimize:raise SystemExit("normal Python mode required; optimized Terraform validation rejected")

ROOT=Path(__file__).resolve().parents[2]
PIN='664b66cc0bcd7ed28fd27569719ccaa8a40c230b8be45060ce4d65e2852e1bcc'
BASE='''terraform { required_version = "= 1.17.0" }
resource "terraform_data" "case" {
  input = { cidr = "10.0.0.0/24", tags = { owner = "service" } }
  LIFECYCLE
}
'''

def run(executable,output):
    EXE=executable.resolve();B=output.resolve()
    assert not B.exists()and not B.is_relative_to(ROOT),'new evidence directory outside source required'
    assert hashlib.sha256(EXE.read_bytes()).hexdigest()==PIN,'pinned Terraform1.17.0 linux_amd64 executable required'
    B.mkdir(parents=True)
    out=B/('run-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir()
    home=out/'isolated-home';home.mkdir();config=home/'terraform.rc';config.write_text('disable_checkpoint = true\n')
    env={'HOME':str(home),'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','TF_CLI_CONFIG_FILE':str(config),'CHECKPOINT_DISABLE':'1','TF_IN_AUTOMATION':'1','TF_INPUT':'0'}
    calls=[]
    def call(cwd,label,args,expected):
        start=datetime.now(timezone.utc).isoformat();so=cwd/(label+'.stdout');se=cwd/(label+'.stderr')
        with so.open('xb')as stdout,se.open('xb')as stderr:
            r=subprocess.run([str(EXE)]+args,cwd=cwd,env=env,stdout=stdout,stderr=stderr,timeout=90)
        row={'label':label,'cwd':str(cwd),'argv':[str(EXE)]+args,'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':r.returncode,'expected_exit_codes':expected,'stdout':str(so),'stderr':str(se)}
        calls.append(row)
        with(out/'commands.jsonl').open('a')as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
        if expected is not None:assert r.returncode in expected,(row,se.read_text())
        return so.read_text(),se.read_text(),r.returncode
    so,_,_=call(out,'00-version',['version','-json'],[0]);observed=json.loads(so);assert observed['terraform_version']=='1.17.0'and observed['platform']=='linux_amd64'
    syntax=[];dirs={}
    variants={'none':'','all':'lifecycle { ignore_changes = all }','tags':'lifecycle { ignore_changes = [input.tags] }','star':'lifecycle { ignore_changes = * }','quoted-star':'lifecycle { ignore_changes = ["*"] }'}
    for name,block in variants.items():
        d=out/name;d.mkdir();dirs[name]=d;(d/'main.tf').write_text(BASE.replace('LIFECYCLE',block))
        call(d,'01-init',['init','-backend=false','-input=false','-no-color'],None)
        so,se,rc=call(d,'02-validate',['validate','-json'],None);v=json.loads(so)
        if name in{'none','all','tags'}:assert rc==0 and v['valid'],(name,v)
        if name=='star':assert rc!=0 and not v['valid']and any('expression'in x['summary'].lower()for x in v['diagnostics']),v
        if name=='quoted-star':assert rc!=0 and not v['valid']and any('wildcard'in x['summary'].lower()for x in v['diagnostics']),v
        syntax.append({'variant':name,'valid':v['valid'],'exit_code':rc,'diagnostics':v['diagnostics']})
    observations=[]
    for mode in('none','all','tags'):
        d=dirs[mode];call(d,'03-initial-plan',['plan','-input=false','-no-color','-refresh=false','-out=initial.tfplan'],[0])
        so,_,_=call(d,'04-initial-json',['show','-json','initial.tfplan'],[0]);plan=json.loads(so)
        assert len(plan['resource_changes'])==1
        for r in plan['resource_changes']:
            assert r['type']=='terraform_data'and r['provider_name']=='terraform.io/builtin/terraform'and r['change']['actions']==['create']
        assert 'provisioner'not in(d/'main.tf').read_text()
        call(d,'05-apply-reviewed-local-plan',['apply','-input=false','-no-color','initial.tfplan'],[0])
        state=d/'terraform.tfstate';original=state.read_bytes();saved=json.loads(original)
        assert len(saved['resources'])==1 and saved['resources'][0]['type']=='terraform_data'
        for scenario in('tags-only','security-cidr'):
            value=copy.deepcopy(saved);attrs=value['resources'][0]['instances'][0]['attributes']
            for field in('input','output'):
                target=attrs[field]['value']
                if scenario=='tags-only':target['tags']['owner']='synthetic-other-controller'
                else:target['cidr']='0.0.0.0/0'
            value['serial']+=1;state.write_text(json.dumps(value)+'\n')
            call(d,'06-'+scenario+'-plan',['plan','-input=false','-no-color','-refresh=false','-out='+scenario+'.tfplan'],[0])
            so,_,_=call(d,'07-'+scenario+'-json',['show','-json',scenario+'.tfplan'],[0]);actual=json.loads(so)
            r=next(x for x in actual['resource_changes']if x['address']=='terraform_data.case');actions=r['change']['actions']
            expected=['no-op']if mode=='all'or(mode=='tags'and scenario=='tags-only')else['update']
            assert actions==expected,(mode,scenario,actions,expected)
            prior=actual['prior_state']['values']['root_module']['resources'][0]['values']['input']
            if scenario=='security-cidr':assert prior['cidr']=='0.0.0.0/0'
            observations.append({'mode':mode,'scenario':scenario,'resource_actions':actions,'known_prior_input':prior,'expected_actions':expected,'unsafe_known_cidr':prior['cidr']=='0.0.0.0/0','scope':'Locally injected built-in state only, refresh disabled. This proves Core update-planning behavior, not real cloud drift or provider refresh.'})
        state.write_bytes(original)
    result={'started_at':calls[0]['started_at'],'ended_at':datetime.now(timezone.utc).isoformat(),'version':'1.17.0','executable_sha256':PIN,'command_calls':len(calls),'syntax_cases':syntax,'state_only_observations':observations,'cloud_providers_or_credentials_used':False,'remote_state_used':False,'source_candidate_modified':False,'scope':'Actual Terraform parser and Core built-in state/planning only. Malformed star syntax is not a semantic security-drift counterexample. Valid all suppresses update proposals but known prior values remain inspectable. No real security-group, cloud-resource or kernel target passed.'}
    (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'directory':str(out),'commands':len(calls),'syntax_cases':len(syntax),'state_only_observations':len(observations),'result':'pass-with-explicit-scope'}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--terraform',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.terraform,args.output)
