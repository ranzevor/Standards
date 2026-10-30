"""A deliberately finite JSON Schema keyword subset, not a full implementation."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
import re,math
from checks.validation_common import require
KEYWORDS={'type','required','additionalProperties','properties','enum','items','minLength','minItems','maxItems','pattern'}
TYPES={'object':dict,'array':list,'string':str,'null':type(None),'boolean':bool,'integer':int,'number':(int,float)}
def json_equal(left,right):
    if type(left) is not type(right):return False
    if type(left) is dict:return set(left)==set(right) and all(json_equal(left[k],right[k]) for k in left)
    if type(left) is list:return len(left)==len(right) and all(json_equal(a,b) for a,b in zip(left,right))
    return left==right

def check_schema(schema):
    require(type(schema) is dict,'finite schema object required')
    require(set(schema)<=KEYWORDS,'unsupported schema keyword',set(schema)-KEYWORDS)
    if 'type' in schema:
        names=schema['type'] if type(schema['type'])is list else [schema['type']]
        require(bool(names) and all(type(name)is str and name in TYPES for name in names)
                and len(names)==len(set(names)),'unsupported or duplicate schema type',schema['type'])
    if 'required' in schema:
        required=schema['required'];require(type(required) is list and all(type(k) is str for k in required) and len(required)==len(set(required)),'finite required unique strings')
    if 'additionalProperties' in schema:require(type(schema['additionalProperties']) is bool,'finite additionalProperties only supports booleans')
    if 'enum' in schema:
        require(type(schema['enum']) is list and bool(schema['enum']),'finite enum nonempty list required')
        for item in schema['enum']:_check(item,{})
        require(not any(json_equal(a,b) for i,a in enumerate(schema['enum']) for b in schema['enum'][i+1:]),'finite enum duplicate value')
    for name in ('minLength','minItems','maxItems'):
        if name in schema:require(type(schema[name]) is int and schema[name]>=0,'finite nonnegative integer bound',name)
    if 'pattern' in schema:
        require(type(schema['pattern']) is str,'finite pattern string required')
        try:re.compile(schema['pattern'])
        except re.error as exc:raise AssertionError('invalid finite pattern') from exc
    if 'properties' in schema:
        require(type(schema['properties']) is dict and all(type(k) is str for k in schema['properties']),'finite properties object required')
        for nested in schema['properties'].values():check_schema(nested)
    if 'items' in schema:check_schema(schema['items'])
    return schema

def _check(value,schema):
    require(type(value) in {dict,list,str,type(None),bool,int,float},'non-JSON value')
    if type(value) is float:require(math.isfinite(value),'nonfinite JSON number')
    if 'type' in schema:
        names=schema['type'] if type(schema['type'])is list else [schema['type']]
        require(any(type(value)in TYPES[name] if isinstance(TYPES[name],tuple) else type(value)is TYPES[name]
                    for name in names),'schema type',names)
    if 'enum' in schema:require(any(json_equal(value,x) for x in schema['enum']),'schema enum')
    if type(value) is dict:
        require(all(type(k) is str for k in value),'JSON object keys must be strings')
        require(set(schema.get('required',[]))<=set(value),'schema required')
        props=schema.get('properties',{})
        if schema.get('additionalProperties') is False:require(set(value)<=set(props),'schema unknown properties')
        for key,v in value.items():
            _check(v,props.get(key,{}))
    if type(value) is list:
        require(len(value)>=schema.get('minItems',0),'schema minItems')
        if 'maxItems' in schema:require(len(value)<=schema['maxItems'],'schema maxItems')
        if 'items' in schema:
            for v in value:_check(v,schema['items'])
        else:
            for v in value:_check(v,{})
    if type(value) is str:
        require(len(value)>=schema.get('minLength',0),'schema minLength')
        if 'pattern' in schema:require(re.search(schema['pattern'],value),'schema pattern')

def schema_check(value,schema):
    """Validate the entire finite schema, including branches absent from data."""
    check_schema(schema)
    _check(value,schema)
