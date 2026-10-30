"""Regressions for the wrong-but-resolvable AI topic references and lookup labels."""
from pathlib import Path
import hashlib
import json
import unittest

from checks.semantic_references import validate_text, validate
from checks.validation_common import ValidationError
from tools.skill_lookup import find
from tools.verify_release_bundle import VerificationError, validate_registry_bytes
from tests.test_release_bundle import fixture_source

ROOT=Path(__file__).resolve().parents[1]

class SemanticReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries=json.loads((ROOT/'registry/standards.json').read_text('utf-8'))
        cls.by_id={row['id']:row for row in cls.entries}
        cls.entry=cls.by_id['STD-L4-AI-AGENT-005']
        cls.target=cls.by_id['STD-L4-AI-AGENT-011']
        cls.label=cls.target['id']+' · '+cls.target['title']
        cls.url=Path(cls.target['path']).name

    def check(self,text):return validate_text(ROOT,self.entry,text,self.entries)

    def test_initial_corpus_exact_identities(self):
        self.assertEqual(validate(ROOT)['documents'],162)
        self.assertEqual({row['version'] for row in self.entries},{'0.1.0'})
        self.assertGreater(self.check('['+self.label+']('+self.url+')'),0)

    def test_resolvable_target_with_wrong_stable_id_is_rejected(self):
        text='['+self.label.replace('-011','-002')+']('+self.url+')'
        with self.assertRaisesRegex(ValidationError,'ID names another'):self.check(text)

    def test_correct_id_with_fluent_wrong_title_is_rejected(self):
        text='['+self.target['id']+' · '+self.by_id['STD-L4-AI-AGENT-007']['title']+']('+self.url+')'
        with self.assertRaisesRegex(ValidationError,'title differs'):self.check(text)

    def test_correct_label_with_other_real_target_is_rejected(self):
        url=Path(self.by_id['STD-L4-AI-AGENT-007']['path']).name
        with self.assertRaisesRegex(ValidationError,'ID names another'):
            self.check('['+self.label+']('+url+')')

    def test_original_005_numeric_label_fails_even_when_link_exists(self):
        with self.assertRaisesRegex(ValidationError,'ordinal names another'):
            self.check('[02 指令信任]('+self.url+')')

    def test_numbered_descriptions_do_not_assert_document_numbers(self):
        for label in ['3 项信任检查','第 3 页','10 个候选','03 项检查','3 个未知对象']:
            with self.subTest(label=label):
                self.assertEqual(self.check('['+label+']('+self.url+')'),1)

    def test_number_and_registered_title_assert_document_identity(self):
        self.assertEqual(self.check('[011 '+self.target['title']+']('+self.url+')'),1)
        with self.assertRaisesRegex(ValidationError,'ordinal names another'):
            self.check('[002 '+self.target['title']+']('+self.url+')')
        with self.assertRaisesRegex(ValidationError,'title differs'):
            self.check('[011 '+self.entry['title']+']('+self.url+')')

    def test_reviewed_legacy_topic_labels_remain_bound_to_current_ids(self):
        for name,old_number,ident in [
            ('指令信任','02','STD-L4-AI-AGENT-011'),
            ('上下文','03','STD-L4-AI-AGENT-007'),
            ('Tool/MCP','06','STD-L4-AI-AGENT-009'),
            ('授权及副作用','07','STD-L4-AI-AGENT-004'),
        ]:
            with self.subTest(name=name):
                url=Path(self.by_id[ident]['path']).name
                with self.assertRaisesRegex(ValidationError,'ordinal names another'):
                    self.check('['+old_number+' '+name+']('+url+')')
                self.assertEqual(self.check('['+ident.rsplit('-',1)[1]+' '+name+']('+url+')'),1)

    def test_verified_numbered_link_is_not_rescanned_as_a_bare_old_ordinal(self):
        self.assertEqual(self.check('[第11 指令信任]('+self.url+')'),1)
        self.assertEqual(self.check('[第11 指令信任][topic]\n\n[topic]: '+self.url+'\n'),1)
        with self.assertRaisesRegex(ValidationError,'ordinal names another'):
            self.check('[第02 指令信任]('+self.url+')')
        with self.assertRaisesRegex(ValidationError,'old AI topic ordinal'):
            self.check('[第11 指令信任]('+self.url+')，另由第05持久记忆管理状态。')

    def test_real_clause_anchor_gives_number_a_clause_meaning(self):
        fragment='#03-有效委派的具体边界'
        self.assertEqual(self.check('[03 有效委派的具体边界]('+self.url+fragment+')'),1)
        # A known short topic label can also describe a numbered clause.
        self.assertEqual(self.check('[02 指令信任]('+self.url+'#02-用户任务与被分析内容分离)'),1)
        with self.assertRaisesRegex(ValidationError,'ordinal names another'):
            self.check('[02 指令信任]('+self.url+'#02-不存在的条款)')
        with self.assertRaisesRegex(ValidationError,'ordinal names another'):
            self.check('[02 指令信任]('+self.url+fragment+')')

    def test_full_document_title_still_asserts_document_number_with_fragment(self):
        with self.assertRaisesRegex(ValidationError,'ordinal names another'):
            self.check('[03 '+self.target['title']+']('+self.url+'#03-有效委派的具体边界)')

    def test_fragment_only_link_binds_current_document_id_and_title(self):
        fragment='#01-最小编排与控制面分离'
        self.assertEqual(self.check('['+self.entry['id']+']('+fragment+')'),1)
        label=self.entry['id']+' · '+self.entry['title']
        self.assertEqual(self.check('['+label+']('+fragment+')'),1)
        with self.assertRaisesRegex(ValidationError,'ID names another'):
            self.check('['+self.target['id']+']('+fragment+')')
        with self.assertRaisesRegex(ValidationError,'title differs'):
            self.check('['+self.entry['id']+' · '+self.target['title']+']('+fragment+')')

    def test_named_fragment_reference_checks_displayed_identity(self):
        definition='\n\n[local]: #01-最小编排与控制面分离\n'
        self.assertEqual(self.check('['+self.entry['id']+'][local]'+definition),1)
        with self.assertRaisesRegex(ValidationError,'ID names another'):
            self.check('['+self.target['id']+'][local]'+definition)

    def test_fragment_reference_and_explicit_self_path_have_same_identity(self):
        fragment='#01-最小编排与控制面分离'
        for url in [fragment,Path(self.entry['path']).name+fragment]:
            with self.subTest(url=url):
                self.assertEqual(self.check('[01 最小编排与控制面分离]('+url+')'),1)
                with self.assertRaisesRegex(ValidationError,'ID names another'):
                    self.check('['+self.target['id']+']('+url+')')

    def test_inline_code_inside_clickable_label_preserves_identity_checks(self):
        for label in ['`'+self.target['id']+'`','`'+self.target['id']+'` · '+self.target['title']]:
            with self.subTest(label=label):
                self.assertEqual(self.check('['+label+']('+self.url+')'),1)
        with self.assertRaisesRegex(ValidationError,'ID names another'):
            self.check('[`STD-L4-AI-AGENT-002`]('+self.url+')')
        with self.assertRaisesRegex(ValidationError,'title differs'):
            self.check('[`'+self.target['id']+'` · '+self.entry['title']+']('+self.url+')')

    def test_named_reference_and_self_fragment_code_labels_preserve_identity(self):
        definition='\n\n[topic]: '+self.url+'\n'
        self.assertEqual(self.check('[`'+self.target['id']+'`][topic]'+definition),1)
        with self.assertRaisesRegex(ValidationError,'ID names another'):
            self.check('[`STD-L4-AI-AGENT-002`][topic]'+definition)
        self.assertEqual(self.check('[`'+self.entry['id']+'`](#01-最小编排与控制面分离)'),1)
        with self.assertRaisesRegex(ValidationError,'ID names another'):
            self.check('[`'+self.target['id']+'`](#01-最小编排与控制面分离)')

    def test_code_label_after_source_citations_keeps_its_actual_link_span(self):
        self.assertEqual(self.check('[S1][S2] [`'+self.target['id']+'`]('+self.url+')'),1)
        with self.assertRaisesRegex(ValidationError,'ID names another'):
            self.check('[S1][S2] [`STD-L4-AI-AGENT-002`]('+self.url+')')
        with self.assertRaisesRegex(ValidationError,'ID names another'):
            self.check('[S1][S2] [`STD-L4-AI-AGENT-002`][topic]\n\n[topic]: '+self.url+'\n')

    def test_whole_link_code_examples_and_comments_remain_literal(self):
        wrong='[STD-L4-AI-AGENT-002]('+self.url+')'
        for text in ['`'+wrong+'`','```md\n'+wrong+'\n```','<!-- '+wrong+' -->',
                     '`example\n'+wrong+'\nend`']:
            with self.subTest(text=text):self.assertEqual(self.check(text),0)
        self.assertEqual(self.check('`'+wrong+'` ['+self.target['id']+']('+self.url+')'),1)

    def test_named_reference_checks_display_text_not_definition_key(self):
        with self.assertRaisesRegex(ValidationError,'ID names another'):
            self.check('['+self.label.replace('-011','-002')+'][topic]\n\n[topic]: '+self.url+'\n')
        self.assertEqual(self.check('['+self.label+'][topic]\n\n[topic]: '+self.url+'\n'),1)

    def test_stable_id_cannot_point_at_an_existing_navigation_file(self):
        with self.assertRaisesRegex(ValidationError,'no registered normative target'):
            self.check('['+self.label+'](README.md)')

    def test_original_015_unlinked_ordinal_is_rejected(self):
        with self.assertRaisesRegex(ValidationError,'old AI topic ordinal'):
            self.check('第05持久记忆处理可跨会话使用的知识。')

    def test_exact_id_only_and_descriptive_links_remain_legal(self):
        self.assertEqual(self.check('['+self.target['id']+']('+self.url+')'),1)
        self.assertEqual(self.check('[指令信任与提示注入防护]('+self.url+')'),1)

    def test_page_references_and_literal_examples_are_not_topics(self):
        self.check('第 3 页、第10次测量、第11条记录。\n\n`第05持久记忆`\n\n'
                   '```md\n第05持久记忆\n```\n\n<!-- 第05持久记忆 -->\n')

    def test_ordinary_counted_objects_are_not_document_references(self):
        self.check('第10个候选、第12组数据、第15位参与者和第01项实验结果均合法。')
        with self.assertRaisesRegex(ValidationError,'old AI topic ordinal'):
            self.check('沿用第10专题的协议约束。')

class ExactLookupTests(unittest.TestCase):
    def test_real_exact_id_returns_bound_title_number_path(self):
        for ident in ['STD-L4-AI-AGENT-005','STD-L4-AI-AGENT-014']:
            result=find(ROOT,document_id=ident)
            self.assertEqual(result['total'],1)
            row=result['results'][0]
            self.assertEqual(row['number'],ident.rsplit('-',1)[1])
            self.assertEqual((ROOT/row['path']).read_text('utf-8').splitlines()[0],'# '+row['title'])

    def test_unknown_exact_id_does_not_fall_back_to_similar_document(self):
        with self.assertRaisesRegex(ValueError,'unknown exact document ID'):
            find(ROOT,document_id='STD-L4-AI-AGENT-099')

    def fixture(self):
        source=fixture_source()
        return source,json.loads(source['registry/standards.json'])

    def test_matching_hash_does_not_validate_wrong_title(self):
        source,rows=self.fixture();rows[0]['title']='看似正确的其他规范名称'
        with self.assertRaisesRegex(VerificationError,'title differs'):
            validate_registry_bytes(rows,source.__getitem__)

    def test_rehashed_wrong_body_id_is_rejected(self):
        source,rows=self.fixture();row=rows[0]
        source[row['path']]=source[row['path']].replace(b'STD-L0-001',b'STD-L0-999')
        row['sha256']=hashlib.sha256(source[row['path']]).hexdigest()
        with self.assertRaisesRegex(VerificationError,'id differs'):
            validate_registry_bytes(rows,source.__getitem__)

    def test_registered_version_must_match_body_even_after_rehash(self):
        source,rows=self.fixture();row=rows[0]
        old=row['path'];row['path']=old.replace('--v0.1.0','--v0.1.2');row['version']='0.1.2'
        source[row['path']]=source.pop(old)
        with self.assertRaisesRegex(VerificationError,'version differs'):
            validate_registry_bytes(rows,source.__getitem__)

    def test_path_number_is_bound_to_id(self):
        source,rows=self.fixture();row=rows[0]
        old=row['path'];row['path']=old.replace('/001-','/999-');source[row['path']]=source.pop(old)
        with self.assertRaisesRegex(VerificationError,'path number differs'):
            validate_registry_bytes(rows,source.__getitem__)

    def test_valid_new_document_revision_can_coexist_with_originals(self):
        source,rows=self.fixture();row=rows[0];old=row['path']
        row['path']=old.replace('--v0.1.0','--v0.1.2');row['version']='0.1.2'
        source[row['path']]=source.pop(old).replace(b'0.1.0',b'0.1.2')
        row['sha256']=hashlib.sha256(source[row['path']]).hexdigest()
        self.assertEqual(validate_registry_bytes(rows,source.__getitem__)[0]['documents'],162)

if __name__=='__main__':unittest.main()
