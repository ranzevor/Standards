"""External JSON contract ambiguity must fail; examples never execute target commands."""
import copy,json,pathlib,subprocess,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from checks.ai_target_contract import inspect_contract
class ContractJSONInputTests(unittest.TestCase):
 def cli(self,script,text,record_option=False):
  with tempfile.TemporaryDirectory()as d:
   path=pathlib.Path(d)/'record.json';path.write_text(text)
   argv=[sys.executable,'-B',str(ROOT/script)]+(['--record']if record_option else[])+[str(path)]
   return subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
 def test_ai_duplicate_lifecycle_field_rejected(self):
  c=json.loads((ROOT/'examples/ai-agent/target-contract.json').read_text());s=json.dumps(c).replace('"implementation_acceptance": "not-run"','"implementation_acceptance":"passed","implementation_acceptance":"not-run"')
  r=self.cli('checks/ai_target_contract.py',s);self.assertNotEqual(r.returncode,0);self.assertIn('duplicate JSON key',r.stderr)
 def test_project_adoption_duplicate_example_identity_rejected(self):
  c=json.loads((ROOT/'examples/adoption-contracts/offline-cli.json').read_text());s=json.dumps(c).replace('"example_only": true','"example_only":false,"example_only":true')
  r=self.cli('checks/project_adoption.py',s,True);self.assertNotEqual(r.returncode,0);self.assertIn('duplicate JSON key',r.stderr)
 def test_nonfinite_nested_schema_rejected_by_cli_and_api(self):
  c=json.loads((ROOT/'examples/ai-agent/target-contract-example.json').read_text());c['input_schema']['properties']['attempt']['default']=float('nan')
  with self.assertRaises(ValueError):inspect_contract(c)
  r=self.cli('checks/ai_target_contract.py',json.dumps(c));self.assertNotEqual(r.returncode,0);self.assertIn('nonfinite JSON',r.stderr)
 def test_adjacent_non_python_local_adapter_and_finite_zero_are_legal(self):
  c=json.loads((ROOT/'examples/ai-agent/target-contract-example.json').read_text());c['adapter_module']='exec:/isolated/adapter';c['run_command']=['/isolated/adapter','run'];c['endpoint']='local://isolated-adapter';c['input_schema']['properties']['attempt']['default']=0
  r=inspect_contract(c);self.assertEqual(r['status'],'not-run');self.assertEqual(r['executed_commands'],[])
  result=self.cli('checks/ai_target_contract.py',json.dumps(c));self.assertEqual(result.returncode,0,result.stderr)
