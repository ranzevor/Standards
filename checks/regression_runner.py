"""Keep local regression stdout/stderr and spawn/exit facts before final aggregation."""
import sys
if sys.flags.optimize:raise RuntimeError('Regression evidence requires normal Python mode; do not use -O or -OO')
from pathlib import Path
from datetime import datetime,timezone
import subprocess,os,json,hashlib

def run_regression(command,*,cwd,env,directory,started,source_identity):
    cwd=Path(cwd).resolve();directory=Path(directory).resolve()
    if directory.is_relative_to(cwd):raise ValueError('regression evidence must be outside source')
    directory.mkdir(parents=True,exist_ok=True)
    stamp=started.strftime('%Y%m%dT%H%M%S.%fZ');prefix=directory/('raw-regression-'+stamp)
    stdout=Path(str(prefix)+'.stdout.log');stderr=Path(str(prefix)+'.stderr.log');events=Path(str(prefix)+'.events.jsonl')
    def event(state,**facts):
        value={'at':datetime.now(timezone.utc).isoformat(),'state':state,'command':command,'cwd':str(cwd),'source_identity':source_identity,**facts}
        with events.open('a',encoding='utf-8')as stream:stream.write(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())
    # Exclusive creation refuses an accidental same-run overwrite or blind retry.
    with events.open('x',encoding='utf-8'):pass
    process=None
    with stdout.open('xb')as out,stderr.open('xb')as err:
        event('launch-pending')
        try:
            process=subprocess.Popen(command,cwd=cwd,env=env,stdout=out,stderr=err)
            event('running',process_id=process.pid)
            code=process.wait()
        except BaseException as error:
            event('launch-failed'if process is None else'wait-interrupted-outcome-unknown',error_type=type(error).__name__,error=str(error),process_id=process.pid if process is not None else None)
            raise
        out.flush();err.flush();os.fsync(out.fileno());os.fsync(err.fileno());event('exited',process_id=process.pid,exit_code=code)
    result=subprocess.CompletedProcess(command,code,stdout.read_text(encoding='utf-8',errors='replace'),stderr.read_text(encoding='utf-8',errors='replace'))
    result.evidence_files=[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in(stdout,stderr,events)]
    return result
