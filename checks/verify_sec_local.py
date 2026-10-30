"""Run bounded local checks with unique receipts; importing this module is inert."""
from datetime import datetime,timezone
from pathlib import Path
import argparse,hashlib,json,os,platform,re,subprocess,sys,tempfile
if sys.flags.optimize:
    print('optimized interpreter rejected for review entry point',file=sys.stderr)
    raise SystemExit(2)

ROOT=Path(__file__).resolve().parents[1]
DOMAINS=('security','embedded-edge','commerce-billing','open-source')
def now():return datetime.now(timezone.utc).isoformat()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def run(root=ROOT,evidence_dir=None):
    root=Path(root).resolve()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    output=Path(evidence_dir) if evidence_dir else Path(tempfile.gettempdir())/'StandardsSecurityValidation'
    output=output.resolve()/stamp
    output.mkdir(parents=True,exist_ok=False)
    selected=[p for domain in DOMAINS for p in (root/'standards/L4'/domain).glob('*--v*.md')]
    selected += [root/'checks'/name for name in ['check_sec_package.py','verify_sec_local.py']]
    selected += list((root/'tests').glob('test_sec_*.py'))
    selected += [p for p in (root/'examples/security-edge-commerce').rglob('*.py') if '__pycache__' not in p.parts]
    identities={p.relative_to(root).as_posix():h(p) for p in sorted(set(selected)) if p.is_file()}
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    commands=[('models-and-direct-binding',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_sec_*.py','-v']),
              ('whole-text-links',[sys.executable,'checks/check_sec_package.py'])]
    receipts=[]
    for key,argv in commands:
        start=now();result=subprocess.run(argv,cwd=root,env=env,text=True,capture_output=True);end=now()
        log=output/(key+'.log');log.write_text(result.stdout+result.stderr)
        row={'id':key,'argv':argv,'cwd':'selected-repository-root','start_utc':start,'end_utc':end,
             'exit_code':result.returncode,'raw_log':log.name,'raw_log_sha256':h(log),
             'scope':'finite synthetic models, isolated local operations and structural bindings; real targets not-run'}
        match=re.search(r'Ran (\d+) tests',result.stdout+result.stderr)
        if match:row['test_methods']=int(match[1])
        receipts.append(row)
        if result.returncode:break
    record={'python':sys.version,'platform':platform.platform(),'object_identities':identities,'commands':receipts,'real_target_status':'not-run'}
    (output/'execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    return record,output

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--evidence-dir',type=Path)
    args=parser.parse_args(argv)
    record,output=run(args.root,args.evidence_dir)
    print(json.dumps({'evidence_dir':str(output),'commands':[{'id':r['id'],'exit_code':r['exit_code'],'test_methods':r.get('test_methods')} for r in record['commands']]},ensure_ascii=False))
    return 0 if len(record['commands'])==2 and all(r['exit_code']==0 for r in record['commands']) else 1

if __name__=='__main__':raise SystemExit(main())
