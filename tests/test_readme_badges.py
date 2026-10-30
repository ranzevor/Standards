import copy
from pathlib import Path
import tempfile
import unittest

from checks.readme_badges import validate_additional_badges, evidence_value, shields_badge_url
from checks.validation_common import ValidationError


class AdditionalBadgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'project.json'; self.source.write_text('{"version":"0.1.1"}')
        self.badge = {'id':'version','kind':'version','object':'Version','claim':'0.1.1',
                      'url':'https://img.shields.io/badge/Version-0.1.1-blue','color':'blue','target':'release.md',
                      'evidence':{'path':'project.json','mode':'json-field','field':'version'}}
        self.contract = {'badge':{'id':'adopted-documents','url':'https://img.shields.io/badge/Documents-162%20adopted-brightgreen'},
                         'additional_badges':[self.badge]}
        self.records = [{'kind':'image','url':self.badge['url'],'parent_url':'release.md','label':'Version: 0.1.1'}]

    def check(self): return validate_additional_badges(self.root,self.records,self.contract)
    def test_source_backed_badge(self): self.assertEqual(self.check(),1)
    def test_contract_without_optional_collection(self):
        self.contract.pop('additional_badges'); self.assertEqual(self.check(),0)
    def test_wrong_destination_fails(self):
        self.records[0]['parent_url']='another.md'
        with self.assertRaisesRegex(ValidationError,'destination'):self.check()
    def test_forged_url_visible_claim_fails(self):
        self.badge['url']=self.badge['url'].replace('0.1.1','0.1.99')
        self.records[0]['url']=self.badge['url']
        with self.assertRaisesRegex(ValidationError,'visible claim'):self.check()
    def test_wrong_source_value_fails(self):
        self.source.write_text('{"version":"0.1.2"}')
        with self.assertRaisesRegex(ValidationError,'source value'):self.check()
    def test_source_format_change_preserves_value(self):
        self.source.write_text('{"version":"0.1.1", "extra":true}')
        self.assertEqual(self.check(),1)
    def test_no_local_badge_or_network_required(self):
        self.assertEqual(list(self.root.iterdir()),[self.source])
        self.assertEqual(self.check(),1)
    def test_non_shields_host_rejected(self):
        self.badge['url']=self.badge['url'].replace('img.shields.io','example.invalid')
        self.records[0]['url']=self.badge['url']
        with self.assertRaisesRegex(ValidationError,'Shields static format'):self.check()
    def test_query_cannot_override_claim(self):
        self.badge['url']+='?label=Certified'
        self.records[0]['url']=self.badge['url']
        with self.assertRaisesRegex(ValidationError,'Shields static format'):self.check()
    def test_accessible_text_must_match_claim(self):
        self.records[0]['label']='Version: 9.9.9'
        with self.assertRaisesRegex(ValidationError,'alternative'):self.check()
    def test_shields_escaping_preserves_literal_hyphens_and_underscores(self):
        self.assertEqual(shields_badge_url('Docs & data','Apache-2.0 / a_b','blue'),
                         'https://img.shields.io/badge/Docs%20%26%20data-Apache--2.0%20%2F%20a__b-blue')
    def test_duplicate_badge_rejected(self):
        self.contract['additional_badges'].append(copy.deepcopy(self.badge))
        with self.assertRaisesRegex(ValidationError,'duplicate'):self.check()
    def test_reference_cannot_be_relabelled_as_certification(self):
        self.badge['kind']='certification'
        with self.assertRaisesRegex(ValidationError,'claim kind'):self.check()
    def test_finite_schema_without_draft_claim_is_valid(self):
        self.source.write_text('{"type":"array","items":{"type":"object"}}')
        e={'path':'project.json','mode':'json-schema'}
        self.assertEqual(evidence_value(self.root,e,'JSON Schema'),'JSON Schema')
    def test_unrelated_json_is_not_schema_evidence(self):
        e={'path':'project.json','mode':'json-schema'}
        with self.assertRaisesRegex(ValidationError,'schema evidence'):evidence_value(self.root,e,'JSON Schema')
    def test_python_value_comes_from_workflow(self):
        self.source.write_text("with:\n  python-version: '3.12'\n")
        e={'path':'project.json','mode':'python-workflow'}
        self.assertEqual(evidence_value(self.root,e,'3.99'),'3.12')
    def test_reference_items_must_exist(self):
        e={'path':'project.json','mode':'references','items':['RFC 8174']}
        with self.assertRaisesRegex(ValidationError,'reference absent'):evidence_value(self.root,e,'RFC 8174')


if __name__=='__main__':unittest.main()
