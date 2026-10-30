"""Actual Linux propagation directions inside a fresh unprivileged user/mount namespace."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,os,subprocess,sys,tempfile,time,platform,hashlib,shutil
if sys.flags.optimize:raise SystemExit("normal Python mode required; optimized mount validation rejected")

def ns(pid='self',kind='mnt'):return os.readlink(f'/proc/{pid}/ns/{kind}')
def encoded(v):return json.dumps(v,ensure_ascii=False,indent=2)+'\n'
def wait_for(path):
    deadline=time.monotonic()+10
    while not path.exists():
        if time.monotonic()>deadline:raise TimeoutError('local namespace handshake')
        time.sleep(.01)

def worker(base,mode,parent):
    assert ns()!=parent['mount_namespace'] and ns(kind='user')==parent['user_namespace']
    assert os.getuid()==0
    source=base/'source';view=base/'view';events=[]
    def call(args,expected=0):
        r=subprocess.run(args,capture_output=True,text=True,timeout=10)
        events.append({'argv':args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        if expected is not None:assert r.returncode==expected,events[-1]
        return r
    call(['mount','--bind',str(source),str(view)])
    call(['mount',{'None':'--make-rprivate','HostToContainer':'--make-rslave','Bidirectional':'--make-rshared'}[mode],str(view)])
    (base/'ready').write_text('ready');wait_for(base/'host-mounted')
    seen=call(['findmnt','-M',str(view/'host'),'-n','-o','FSTYPE'],None)
    (view/'shared.txt').write_text('ordinary shared file write')
    call(['mount','-t','tmpfs','-o','size=1m,nosuid,nodev,noexec','tmpfs',str(view/'child')])
    (base/'child-mounted').write_text('ready');wait_for(base/'parent-observed')
    call(['umount',str(view/'child')]);call(['umount',str(view)])
    return {'mode':mode,'mount_namespace':ns(),'user_namespace':ns(kind='user'),'host_mount_received':seen.returncode==0,'commands':events}

def isolated(base,parent):
    # The parent is the ordinary launcher. A direct accidental --isolated call
    # in the same user/mount namespace is rejected before any mount operation.
    assert ns()!=parent['mount_namespace'] and ns(kind='user')!=parent['user_namespace']
    mapping=Path('/proc/self/uid_map').read_text().split()
    assert os.getuid()==0 and len(mapping)==3 and mapping[0]=='0'and mapping[2]=='1'
    all_cases=[]
    for mode in ['None','HostToContainer','Bidirectional']:
        d=base/mode;d.mkdir();source=d/'source';view=d/'view';source.mkdir();view.mkdir();events=[]
        def call(args,expected=0):
            r=subprocess.run(args,capture_output=True,text=True,timeout=10)
            events.append({'argv':args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
            if expected is not None:assert r.returncode==expected,events[-1]
            return r
        call(['mount','-t','tmpfs','-o','size=1m,nosuid,nodev,noexec','tmpfs',str(source)])
        for name in ['host','child']:(source/name).mkdir()
        (source/'shared.txt').write_text('initial')
        call(['mount','--make-rshared',str(source)])
        args=['unshare','--mount','--propagation','unchanged',sys.executable,'-B',str(Path(__file__).resolve()),'--worker',mode,'--base',str(d),'--parent-namespaces',json.dumps({'mount_namespace':ns(),'user_namespace':ns(kind='user')})]
        with (d/'worker.stdout').open('w')as so,(d/'worker.stderr').open('w')as se:
            proc=subprocess.Popen(args,stdout=so,stderr=se)
            wait_for(d/'ready');call(['mount','-t','tmpfs','-o','size=1m,nosuid,nodev,noexec','tmpfs',str(source/'host')]);(d/'host-mounted').write_text('ready')
            wait_for(d/'child-mounted');outward=call(['findmnt','-M',str(source/'child'),'-n','-o','FSTYPE'],None)
            ordinary_write=(source/'shared.txt').read_text()
            call(['umount',str(source/'host')]);(d/'parent-observed').write_text('observed')
            assert proc.wait(timeout=15)==0,(d/'worker.stderr').read_text()
        child=json.loads((d/'worker.stdout').read_text());assert child['host_mount_received']==(mode!='None'),child
        assert (outward.returncode==0)==(mode=='Bidirectional'),events
        assert ordinary_write=='ordinary shared file write'
        call(['umount',str(source)])
        all_cases.append({'mode':mode,'host_to_view_mount_received':child['host_mount_received'],'view_to_host_mount_received':outward.returncode==0,'ordinary_file_write_shared':True,'worker':child,'outer_commands':events,'worker_stderr':(d/'worker.stderr').read_text()})
    return {'started_in_private_user_and_mount_namespace':True,'fake_host_mount_namespace':ns(),'user_namespace':ns(kind='user'),'uid_map':Path('/proc/self/uid_map').read_text(),'cases':all_cases,'scope':'Actual Linux tmpfs/bind propagation only, entirely below the new private outer mount namespace. Not a Kubernetes/CSI/runtime/real-host isolation result.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--isolated',action='store_true');ap.add_argument('--worker',choices=['None','HostToContainer','Bidirectional']);ap.add_argument('--base',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--parent-namespaces',type=json.loads);a=ap.parse_args()
    if a.worker:print(encoded(worker(a.base,a.worker,a.parent_namespaces)));return
    if a.isolated:print(encoded(isolated(a.base,a.parent_namespaces)));return
    assert a.output and not a.output.exists()
    repository=Path(__file__).resolve().parents[2]
    assert not a.output.resolve().is_relative_to(repository),'keep generated evidence outside source'
    a.output.mkdir(parents=True)
    before={'mount_namespace':ns(),'user_namespace':ns(kind='user')};start=datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix='StandardsMountDirections-')as tmp:
        cmd=['unshare','--user','--map-root-user','--mount','--propagation','private',sys.executable,'-B',str(Path(__file__).resolve()),'--isolated','--base',tmp,'--parent-namespaces',json.dumps(before)]
        env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'}
        r=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=90)
        (a.output/'isolated.stdout').write_text(r.stdout);(a.output/'isolated.stderr').write_text(r.stderr)
        tools={}
        for name in ['unshare','mount','umount','findmnt']:
            exe=Path(shutil.which(name)).resolve();v=subprocess.run([str(exe),'--version'],capture_output=True,text=True,timeout=10)
            tools[name]={'path':str(exe),'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'version_stdout':v.stdout,'version_stderr':v.stderr,'exit_code':v.returncode}
        parent_points=[]
        for mode in ['None','HostToContainer','Bidirectional']:
            for item in ['source','view']:
                q=str(Path(tmp)/mode/item);v=subprocess.run(['findmnt','-M',q,'-n','-o','TARGET'],capture_output=True,text=True,timeout=10)
                parent_points.append({'path':q,'exit_code':v.returncode,'stdout':v.stdout,'stderr':v.stderr})
                assert v.returncode==1 and not v.stdout,'unexpected probe mount in launcher namespace'
        metadata={'tools':tools,'kernel':dict(platform.uname()._asdict()),'launcher_probe_mount_checks':parent_points,'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'argv':cmd,'exit_code':r.returncode,'launcher_namespace_before':before,'launcher_namespace_after':{'mount_namespace':ns(),'user_namespace':ns(kind='user')},'source_modified':False,'actual_global_host_mounts_created':False}
        (a.output/'execution.json').write_text(encoded(metadata));assert r.returncode==0,r.stderr
        value=json.loads(r.stdout);assert len(value['cases'])==3 and metadata['launcher_namespace_before']==metadata['launcher_namespace_after']
        (a.output/'results.json').write_text(encoded(value));print(encoded({'output':str(a.output),'modes':3,'result':'pass-local-namespaces-only'}))

if __name__=='__main__':main()
