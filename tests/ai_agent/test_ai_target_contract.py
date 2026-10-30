import sys,pathlib,unittest,json,copy
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from checks.ai_target_contract import inspect_contract,FIELDS
class TargetContractTests(unittest.TestCase):
    def setUp(self):self.c=json.loads((ROOT/'examples/ai-agent/target-contract.json').read_text())
    def test_unconfigured_not_pass(self):self.assertEqual(inspect_contract(self.c)['status'],'not-run');self.assertEqual(inspect_contract(self.c)['executed_commands'],[])
    def test_fabricated_pass_rejected(self):
        self.c['implementation_acceptance']='passed'
        with self.assertRaises(ValueError):inspect_contract(self.c)
    def test_configured_still_not_executed(self):
        self.c=json.loads((ROOT/'examples/ai-agent/target-contract-example.json').read_text());self.c['target_kind']='configured-real-target'
        self.assertEqual(inspect_contract(self.c)['contract_configuration'],'configured-not-executed');self.assertEqual(inspect_contract(self.c)['status'],'not-run')

    def test_nonempty_wrong_types_are_rejected(self):
        c=json.loads((ROOT/'examples/ai-agent/target-contract-example.json').read_text())
        for field in FIELDS:
            with self.subTest(field=field):
                bad=copy.deepcopy(c);bad[field]={'reference':{}} if field=='exact_versions' else {'reference':'synthetic-config-only'}
                with self.assertRaises(ValueError):inspect_contract(bad)
    def test_partial_configuration_is_not_an_unconfigured_legal_neighbor(self):
        self.c['run_command']=['python','adapter.py']
        with self.assertRaises(ValueError):inspect_contract(self.c)
    def test_example_has_no_execution_or_real_configuration_claim(self):
        c=json.loads((ROOT/'examples/ai-agent/target-contract-example.json').read_text());r=inspect_contract(c)
        self.assertEqual(r['contract_configuration'],'example-only-not-executed');self.assertEqual(r['executed_commands'],[])
    def test_unknown_keys_and_boolean_version_are_rejected(self):
        for change in ({'schema_version':True},{'unexpected':1}):
            c=copy.deepcopy(self.c);c.update(change)
            with self.assertRaises(ValueError):inspect_contract(c)
    def test_zero_boolean_budget_and_unpinned_version_rejected(self):
        c=json.loads((ROOT/'examples/ai-agent/target-contract-example.json').read_text())
        for value in (0,True,-1):
            bad=copy.deepcopy(c);bad['budget_bound_and_usage_source']['maximum_units']=value
            with self.assertRaises(ValueError):inspect_contract(bad)
        for value in ('latest','^1.2.3','*'):
            bad=copy.deepcopy(c);bad['exact_versions']['adapter']=value
            with self.assertRaises(ValueError):inspect_contract(bad)
