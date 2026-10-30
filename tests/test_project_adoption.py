import copy
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tests.platform_support import make_symlink
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('project_adoption',ROOT/'checks/project_adoption.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
H='a'*64
CAT=[{'id':'a','version':'0.1','sha256':H,'path':'standards/a--v0.1.md'},{'id':'b','version':'0.1','sha256':'b'*64,'path':'standards/b--v0.1.md'}]
CLAUSES=[{'document_id':'a','clause_id':'M01'},{'document_id':'b','clause_id':'M01'}]
def fixture():
 return {'schema_version':'1.0','id':'Synthetic','example_only':True,'operation_authorized':False,'project':{'id':'SyntheticOffline','kind':'synthetic'},'decision':{'status':'not-decided','actor':None,'authority_reference':None,'at':None},'standards':[dict(CAT[0],selection='technical-reference')],'requirements':[{'document_id':'a','clause_id':'M01','applicability':'applicable','reason':'local file conversion exists','checks':[{'id':'check-1','evidence_level':'isolated-implementation','command':'python synthetic_converter.py valid.json','expected':'exit 0 and exact normalized output','actual':None,'status':'not-run','evidence':[]}]}],'dependencies':[],'implementation':{'status':'not-run','identity':'synthetic-design-only','environment':'not-selected','scope':'selective interface example, not complete project conformance'}}
class ProjectAdoption(unittest.TestCase):
 def valid(self,x):return model.validate_record(x,CAT,CLAUSES)
 def reject(self,x):
  with self.assertRaises(ValueError):self.valid(x)
 def test_positive(self):self.assertEqual(self.valid(fixture())['documents'],1)
 def test_legal_empty_selection(self):
  x=fixture();x['standards']=[];x['requirements']=[];self.assertEqual(self.valid(x)['selected_requirements'],0)
 def test_legal_no_account_not_applicable(self):
  x=fixture();x['requirements'][0].update(applicability='not-applicable',reason='no account or network functionality',checks=[]);self.valid(x)
 def test_undetermined_is_not_runtime_pass(self):
  x=fixture();x['requirements'][0]['applicability']='undetermined';x['implementation']['status']='pass';self.reject(x)
 def test_hash_version_path_drift(self):
  for field,value in [('sha256','c'*64),('version','0.2'),('path','../escape.md')]:
   x=fixture();x['standards'][0][field]=value;self.reject(x)
 def test_duplicate_documents_and_clauses(self):
  for field in ['standards','requirements']:
   x=fixture();x[field].append(copy.deepcopy(x[field][0]));self.reject(x)
 def test_unknown_clause_and_cross_document_binding(self):
  x=fixture();x['requirements'][0]['clause_id']='M02';self.reject(x)
  x=fixture();x['requirements'][0]['document_id']='b';self.reject(x)
 def test_clause_index_requires_canonical_document_and_clause_ids(self):
  for row in ({'id':'M01'}, {'standard_id':'a','local_id':'M01'}, {'document_id':'a','clause_id':''}):
   with self.subTest(row=row),self.assertRaisesRegex(ValueError,'canonical document and clause identities'):
    model.validate_record(fixture(),CAT,[row])
 def test_product_example_rejects_clause_index_without_document_identity(self):
  from checks.validate_product import validate_adoption
  from checks.validation_common import ValidationError
  record={'schema_version':'2','example_only':True,'operation_authorized':False,
          'project':'SyntheticOffline','scope':'local file conversion','environment':'local-synthetic',
          'standards':[{key:CAT[0][key] for key in ('id','version','sha256')}],
          'requirements':[{'document_id':'a','clause_id':'M01','applicability':'applicable',
                           'object':'synthetic CSV','check':'verify output fields','expected':'correct output',
                           'status':'not-run','actual':None}]}
  self.assertEqual(validate_adoption(record,CAT,CLAUSES),1)
  with self.assertRaisesRegex(ValidationError,'canonical document and clause identities'):
   validate_adoption(record,CAT,[{'id':'M01'}])
 def test_undecided_cannot_invent_actor(self):
  x=fixture();x['decision']['actor']='named-role';self.reject(x)
 def test_example_cannot_adopt_or_authorize(self):
  x=fixture();x['operation_authorized']=True;self.reject(x)
  x=fixture();x['decision'].update(status='adopted',actor='not-real',authority_reference='label',at='2026-10-23T00:00:00Z');self.reject(x)
 def test_adopted_selection_requires_attributed_decision(self):
  x=fixture();x['standards'][0]['selection']='adopted';self.reject(x)
 def test_not_run_has_no_actual_or_evidence(self):
  for field,value in [('actual','success'),('evidence',['made-up-log'])]:
   x=fixture();x['requirements'][0]['checks'][0][field]=value;self.reject(x)
 def test_keyword_pass_is_not_evidence(self):
  x=fixture();x['example_only']=False;x['project']['kind']='real-project';x['requirements'][0]['checks'][0]['status']='pass';self.reject(x)
 def test_structural_pass_is_not_real_implementation(self):
  x=fixture();x['example_only']=False;x['project']['kind']='real-project';c=x['requirements'][0]['checks'][0];c.update(status='pass',actual='only schema fields checked',evidence=['actual-local-schema-log'],evidence_level='document-structure');x['implementation']['status']='pass';self.reject(x)
 def test_nonempty_reason_and_check_contract(self):
  for change in ['reason','checks']:
   x=fixture();x['requirements'][0][change]='' if change=='reason' else [];self.reject(x)
 def both(self):
  x=fixture();x['standards'].append(dict(CAT[1],selection='technical-reference'));r=copy.deepcopy(x['requirements'][0]);r['document_id']='b';x['requirements'].append(r);return x
 def edge(self,a,b,kind='required-consumption'):
  return {'from':{'document_id':a,'clause_id':'M01'},'to':{'document_id':b,'clause_id':'M01'},'interface':'provider returns authoritative result for original intent','kind':kind}
 def test_dependency_closure_and_duplicate(self):
  x=self.both();x['dependencies']=[self.edge('a','b')];self.valid(x)
  x['requirements'][1]['applicability']='not-applicable';self.reject(x)
  x=self.both();x['dependencies']=[self.edge('a','b')]*2;self.reject(x)
 def test_necessary_cycle_rejected_reference_cycle_legal(self):
  x=self.both();x['dependencies']=[self.edge('a','b'),self.edge('b','a')];self.reject(x)
  x['dependencies']=[self.edge('a','b','technical-reference'),self.edge('b','a','technical-reference')];self.valid(x)
 def test_missing_endpoint_and_self_edge(self):
  x=fixture();x['dependencies']=[self.edge('a','b')];self.reject(x)
  x['dependencies']=[self.edge('a','a')];self.reject(x)
 def test_unknown_field_and_invalid_boolean(self):
  x=fixture();x['approved']=True;self.reject(x)
  x=fixture();x['operation_authorized']=0;self.reject(x)
 def test_timestamp_needs_zone(self):
  x=fixture();x['example_only']=False;x['project']['kind']='real-project';x['decision'].update(status='adopted',actor='a',authority_reference='external-unverified-reference',at='2026-10-23T00:00:00');self.reject(x)
 def test_path_boundary_and_symlink(self):
  with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
   root=Path(d);(root/'local').write_text('ok');outside=Path(other)/'secret';outside.write_text('synthetic');make_symlink(root/'link', outside)
   self.assertEqual(model.safe_file(root,'local').read_text(),'ok')
   for path in ['../escape',str(outside),'link','a\\b']:
    with self.assertRaises(ValueError):model.safe_file(root,path)
 def test_optimized_subprocess_rejected(self):
  for flag in ['-O','-OO']:
   proc=subprocess.run([sys.executable,flag,str(ROOT/'checks/project_adoption.py'),'--help'],capture_output=True,text=True)
   self.assertNotEqual(proc.returncode,0);self.assertIn('do not use -O',proc.stderr)
if __name__=='__main__':unittest.main()
