"""Inspect a real-target contract; never executes its command or infers a platform pass."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
import json,pathlib,sys,re
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from checks.validation_common import read_json
FIELDS=('adapter_module','run_command','endpoint','exact_versions','authenticated_subject_source','input_schema','output_schema','authority_query','idempotency_scope_and_window','current_authorization_and_fence_acceptance_point','logical_task_attempt_epoch_mapping','budget_bound_and_usage_source','cancellation_and_unknown_result_contract')
def inspect_contract(c):
    json.dumps(c,allow_nan=False)
    if not isinstance(c,dict)or type(c.get('schema_version'))is not int or c['schema_version']!=1:raise ValueError('unsupported contract schema')
    if set(c)!=set(FIELDS)|{'schema_version','target_kind','implementation_acceptance','test_layers','evidence_receipts'}:raise ValueError('missing or unknown contract keys')
    kind=c['target_kind']
    if kind not in ('unconfigured-real-target','configured-real-target','synthetic-example'):raise ValueError('unknown target kind')
    missing=[k for k in FIELDS if c[k]is None or c[k]=={}]
    if c.get('implementation_acceptance')!='not-run':raise ValueError('this inspector cannot attest a real-target run')
    layers=c.get('test_layers',{})
    required=('actual_model_behavior','actual_sdk_protocol','actual_storage_auth_isolation','actual_business_result')
    if not isinstance(layers,dict)or set(layers)!=set(required)|{'finite_reference_model'}:raise ValueError('invalid layer keys')
    if any(layers[k]!='not-run'for k in required)or layers['finite_reference_model']!='separate-local-evidence':raise ValueError('unattested real layer')
    if c['evidence_receipts']!=[]:raise ValueError('unexecuted contract cannot introduce execution receipts')
    if missing:
        if kind!='unconfigured-real-target'or len(missing)!=len(FIELDS):raise ValueError('partially configured contract is ambiguous')
        return {'status':'not-run','contract_configuration':'incomplete','missing_fields':missing,'executed_commands':[]}
    if kind=='unconfigured-real-target':raise ValueError('configured fields require configured or example kind')
    def text(v,key):
        if not isinstance(v,str)or not v.strip():raise ValueError(key+' must be a nonempty string')
    def strings(v,key):
        if not isinstance(v,list)or not v or any(not isinstance(s,str)or not s.strip()for s in v):raise ValueError(key+' must be a nonempty string array')
    text(c['adapter_module'],'adapter_module')
    if not(re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*',c['adapter_module'])or re.fullmatch(r'[a-z][a-z0-9+.-]*:.+',c['adapter_module'])):raise ValueError('adapter module or explicit L5 adapter locator required')
    strings(c['run_command'],'run_command');text(c['endpoint'],'endpoint')
    from urllib.parse import urlsplit
    uri=urlsplit(c['endpoint'])
    if not uri.scheme or not(uri.netloc or uri.path):raise ValueError('endpoint must be an explicit URI')
    if not isinstance(c['exact_versions'],dict)or not c['exact_versions']:raise ValueError('exact_versions must be nonempty object')
    for name,version in c['exact_versions'].items():
        text(name,'version component');text(version,'version value')
        if version.lower()in('latest','stable','*')or any(x in version for x in '^~<>*'):raise ValueError('versions must be exact')
    for key in ('input_schema','output_schema'):
        schema=c[key]
        if not isinstance(schema,dict)or schema.get('type')!='object'or not isinstance(schema.get('properties'),dict):raise ValueError(key+' must be object schema')
        names=schema.get('required',[])
        if not isinstance(names,list)or any(not isinstance(x,str)for x in names)or not set(names)<=set(schema['properties']):raise ValueError('invalid required property names')
    structures={
      'authenticated_subject_source':('authority','input_claims','validation_command'),
      'authority_query':('command','result_fields','unavailable_action'),
      'idempotency_scope_and_window':('key_fields','retention_seconds','authority'),
      'current_authorization_and_fence_acceptance_point':('authenticated_subject_fields','permission_source','fence_field','atomic_acceptance_point','denial_action'),
      'logical_task_attempt_epoch_mapping':('task_field','attempt_field','epoch_field','stale_result_action'),
      'budget_bound_and_usage_source':('maximum_units','unit','reservation_authority','usage_authority','unknown_result_action'),
      'cancellation_and_unknown_result_contract':('cancel_command','query_command','terminal_states','unknown_action','retry_condition','timeout_seconds')}
    arrays={'input_claims','validation_command','command','result_fields','key_fields','authenticated_subject_fields','cancel_command','query_command','terminal_states'}
    integers={'retention_seconds','maximum_units','timeout_seconds'}
    for key,required_keys in structures.items():
        obj=c[key]
        if not isinstance(obj,dict)or set(obj)!=set(required_keys):raise ValueError(key+' has missing or unknown fields')
        for name,value in obj.items():
            if name in arrays:strings(value,key+'.'+name)
            elif name in integers:
                if type(value)is not int or value<=0:raise ValueError(key+'.'+name+' must be a positive integer')
            else:text(value,key+'.'+name)
    return {'status':'not-run','contract_configuration':'example-only-not-executed'if kind=='synthetic-example'else'configured-not-executed','missing_fields':[],'executed_commands':[],'semantic_contract_review':'required','validation_scope':'finite field format; commands, service identity, permissions and behavior are not executed'}
if __name__=='__main__':
    path=pathlib.Path(sys.argv[1])if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[1]/'examples/ai-agent/target-contract.json'
    print(json.dumps(inspect_contract(read_json(path)),ensure_ascii=False))
