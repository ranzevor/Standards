"""Run installed local stack fixtures; never install tools or contact services."""
from __future__ import annotations
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
import argparse,base64,datetime,hashlib,json,math,os,shutil,subprocess,tempfile,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def positive_timeout(value):
    try:seconds=float(value)
    except (TypeError,ValueError) as error:raise ValueError('timeout must be a positive finite number of seconds') from error
    if isinstance(value,bool) or not math.isfinite(seconds) or seconds<=0:
        raise ValueError('timeout must be a positive finite number of seconds')
    return seconds

def capture(value):
    observed=value is not None
    if value is None:data=b''
    elif isinstance(value,bytes):data=value
    elif isinstance(value,str):data=value.encode('utf-8')
    else:raise TypeError('unsupported captured stream value')
    return {'text':data.decode('utf-8',errors='replace'),'base64':base64.b64encode(data).decode('ascii'),
            'sha256':hashlib.sha256(data).hexdigest(),'capture_observed':observed}

def run(command,cwd,expected=None,expected_code=0,env=None,timeout_seconds=40):
    seconds=positive_timeout(timeout_seconds)
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    code=None;error=None
    try:
        process=subprocess.run(command,cwd=cwd,env=env,capture_output=True,timeout=seconds)
        outcome='completed';code=process.returncode;stdout=capture(process.stdout);stderr=capture(process.stderr)
    except subprocess.TimeoutExpired as failure:
        outcome='timed-out';stdout=capture(failure.stdout);stderr=capture(failure.stderr)
        error={'type':'TimeoutExpired','message':'command exceeded the configured timeout; exit code unavailable in this exception'}
    except OSError as failure:
        outcome='launch-failed';stdout=capture(None);stderr=capture(None)
        error={'type':type(failure).__name__,'message':str(failure),'errno':failure.errno}
    result={'command':list(command),'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'outcome':outcome,'timeout_seconds':seconds,'exit_code':code,'expected_exit_code':expected_code,
            'stdout':stdout['text'],'stderr':stderr['text'],'stdout_base64':stdout['base64'],'stderr_base64':stderr['base64'],
            'stdout_sha256':stdout['sha256'],'stderr_sha256':stderr['sha256'],
            'stdout_capture_observed':stdout['capture_observed'],'stderr_capture_observed':stderr['capture_observed'],
            'text_decoding':'UTF-8 with replacement; observed raw bytes retained as base64 and SHA256','error':error}
    result['pass']=outcome=='completed' and code==expected_code and (expected is None or expected in result['stdout'])
    return result

def collect(results,unrun,timeout_seconds):
    def execute(*args,**kwargs):
        return run(*args,**kwargs,timeout_seconds=timeout_seconds)
    with tempfile.TemporaryDirectory(prefix='standards-stacks-') as tmp:
        work=Path(tmp);env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',XDG_CACHE_HOME=str(work/'cache'),XDG_DATA_HOME=str(work/'data'))
        for script,marker in [('python_case.py','python-contract-ok'),('sqlite_case.py','sqlite-contract-ok')]:
            results.append(execute([sys.executable,str(ROOT/script)],work,marker,env=env))
        node=shutil.which('node')
        if node:
            results.append(execute([node,'--version'],work,env=env))
            results.append(execute([node,str(ROOT/'javascript_case.mjs')],work,'javascript-contract-ok',env=env))
        else:unrun.append({'stack':'javascript-runtime','reason':'node not installed'})
        for compiler,src,standard,marker in [('gcc','native_case.c','c17','c-contract-ok'),('g++','native_case.cpp','c++20','cpp-contract-ok')]:
            tool=shutil.which(compiler)
            if not tool:unrun.append({'stack':standard,'reason':compiler+' not installed'});continue
            results.append(execute([tool,'--version'],work,env=env));binary=work/standard
            build=execute([tool,'-std='+standard,'-Wall','-Wextra','-Werror','-O2',str(ROOT/src),'-o',str(binary)],work,env=env);results.append(build)
            if build['pass']:results.append(execute([str(binary)],work,marker,env=env))
        bash=shutil.which('bash')
        if bash:
            results.append(execute([bash,'--version'],work,env=env))
            value='含 空格; $(not-a-command) * '
            for args,code in [([value],0),([],64),(['a','b'],64)]:
                r=execute([bash,str(ROOT/'shell_case.sh'),*args],work,expected_code=code,env=env)
                if code==0:r['pass']=r['pass'] and r['stdout']==value+'\n'
                results.append(r)
        else:unrun.append({'stack':'bash','reason':'bash not installed'})
        godot=shutil.which('godot')
        if godot:
            results.append(execute([godot,'--version'],work,env=env))
            # Copy fixtures so engine caches/import metadata never alter tracked files.
            gd=work/'godot';gd.mkdir()
            for name in ['project.godot','godot_case.gd']:shutil.copyfile(ROOT/name,gd/name)
            results.append(execute([godot,'--headless','--path',str(gd),'--script',str(gd/'godot_case.gd')],work,'godot-contract-ok',env=env))
        else:unrun.append({'stack':'godot','reason':'godot not installed'})

def validate(timeout_seconds=40):
    seconds=positive_timeout(timeout_seconds);results=[];unrun=[];errors=[]
    try:collect(results,unrun,seconds)
    except Exception as error:
        errors.append({'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc(),
                       'remaining_fixtures':'not attempted after fixture orchestration error; no availability or success inferred'})
    unrun.extend([
        {'stack':'typescript','reason':'not executed by this fixture; JavaScript runtime checks do not establish TypeScript type-check acceptance'},
        {'stack':'jvm-java-kotlin','reason':'not compiled or executed by this fixture; run the exact selected JDK/Kotlin target contract separately'},
        {'stack':'go','reason':'not executed by this fixture; establish actual Go toolchain identity before running the target contract'},
        {'stack':'rust','reason':'not executed by this fixture; run the selected rustc/cargo target and feature contract separately'},
        {'stack':'dotnet','reason':'not executed by this fixture; run the selected SDK/TFM/RID target contract separately'},
        {'stack':'powershell','reason':'not executed by this fixture; Bash argv checks do not establish PowerShell behavior'},
        {'stack':'browsers-devices-services','reason':'these local fixtures do not execute real browsers, assistive technology, devices, network services or payments'}])
    return {'scope':'actual installed local runtimes and finite fixtures only; command outcomes do not establish external side-effect or descendant-process state',
            'results':results,'not_run':unrun,'fixture_errors':errors,'implementation_acceptance':'not-run','pass':not errors and all(r['pass'] for r in results),
            'fixture_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.iterdir()) if p.is_file() and p.suffix in {'.py','.mjs','.c','.cpp','.sh','.gd','.godot'}}}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path)
    parser.add_argument('--timeout-seconds',type=positive_timeout,default=40,help='positive finite per-command limit, default 40 seconds')
    args=parser.parse_args(argv)
    if args.report:
        if args.report.resolve().is_relative_to(ROOT.parents[1]):parser.error('report must be outside the fixture source repository')
        if args.report.exists():parser.error('report already exists; choose a new path to preserve earlier evidence')
    report=validate(args.timeout_seconds);text=json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if args.report:
        try:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            with args.report.open('x',encoding='utf-8') as handle:handle.write(text)
        except OSError as error:
            print(text);print('report publication failed: '+str(error),file=sys.stderr);return 2
    print(text);return 0 if report['pass'] else 1

if __name__=='__main__':
    raise SystemExit(main())
