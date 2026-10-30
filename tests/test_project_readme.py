"""Direct broken artifacts and valid neighboring forms; no word-count quality test."""
import copy
import tempfile
from pathlib import Path
import unittest
from tests.platform_support import make_symlink
from checks.project_readme import (parse_links, validate_document_links, validate_readmes,
                                   validate_translations, resolve_target, validate, ROOT)
from checks.validation_common import ValidationError, digest

SVG = '''<svg xmlns="http://www.w3.org/2000/svg"><title>Brand</title><desc>Example project cover</desc><text>Example</text></svg>'''


class ReadmeFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.write('assets/cover.svg', SVG)
        self.write('registry/standards.json', '[{"id":"STD-EXAMPLE-001","status":"adopted"}]')
        self.badge_url = 'https://img.shields.io/badge/Documents-1%20adopted-brightgreen'
        self.write('guide.md', '# Guide\n\n<a id="target"></a>\n## Detail\n')
        for name, other in [('README.md', 'README.en.md'), ('README.en.md', 'README.md')]:
            self.write(name, f'''# Example

![Brand](assets/cover.svg)
[![Documents: 1 adopted]({self.badge_url})](#status)

[Language]({other})

<a id="status"></a>
## State

[Guide][guide]

```sh
python check.py
```

[guide]: guide.md#target
''')
        self.contract = {'badge_protocol':'shields-static/1',
                         'files': {'zh-Hans': 'README.md', 'en': 'README.en.md'},
                         'anchors': ['status'], 'navigation': {'guide': {'zh-Hans': 'guide.md#target', 'en': 'guide.md#target'}},
                         'shell_blocks': ['python check.py'],
                         'images': [{'path': 'assets/cover.svg', 'sha256': digest((self.root/'assets/cover.svg').read_bytes())}],
                         'badge': {'id':'adopted-documents','kind':'status','object':'Documents',
                                   'claim':'1 adopted','url':self.badge_url,'color':'brightgreen','target':'#status',
                                   'evidence':{'path':'registry/standards.json','mode':'adopted-documents'}}}
    def write(self, name, value):
        p = self.root/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(value, encoding='utf-8'); return p
    def change(self, old, new, name='README.md'):
        p = self.root/name; self.assertIn(old, p.read_text()); p.write_text(p.read_text().replace(old, new))
    def check(self): return validate_readmes(self.root, self.contract)
    def bad(self, reason):
        with self.assertRaisesRegex(ValidationError, reason): self.check()

    def test_real_bilingual_contract_positive(self):
        self.assertEqual(self.check()['files'], 2)
    def test_removing_badge_protocol_cannot_disable_shields_requirement(self):
        self.contract.pop('badge_protocol')
        self.bad('Shields badge protocol is required')
    def test_old_local_svg_protocol_cannot_replace_shields(self):
        self.contract['badge_protocol']='local-svg/1'
        self.bad('Shields badge protocol is required')
    def test_removing_collection_contract_cannot_disable_badge_checks(self):
        self.contract.pop('badge')
        self.bad('collection badge contract is required')
    def test_local_svg_cannot_replace_standard_badge_after_contract_rebind(self):
        self.write('assets/replacement.svg', SVG)
        for name in ('README.md', 'README.en.md'):
            self.change(self.badge_url, 'assets/replacement.svg', name)
        self.contract['badge']['url']='assets/replacement.svg'
        self.bad('Shields static format')
    def test_missing_image_direct_failure(self):
        self.change('assets/cover.svg', 'assets/missing.svg'); self.bad('missing target')
    def test_empty_alt_direct_failure(self):
        self.change('![Brand]', '![]'); self.bad('alternative')
    def test_entity_only_alt_is_empty(self):
        self.change('![Brand]', '![&#32;]'); self.bad('alternative')
    def test_empty_link_label_direct_failure(self):
        self.change('[Guide][guide]', '[][guide]'); self.bad('empty link name')
    def test_reference_definition_is_not_navigation(self):
        self.change('[Guide][guide]', 'Guide'); self.bad('missing named navigation')
    def test_code_fence_does_not_satisfy_navigation(self):
        self.change('[Guide][guide]', '```text\n[Guide][guide]\n```'); self.bad('missing named navigation')
    def test_inline_code_does_not_satisfy_navigation(self):
        self.change('[Guide][guide]', '`[Guide][guide]`'); self.bad('missing named navigation')
    def test_comment_does_not_satisfy_navigation(self):
        self.change('[Guide][guide]', '<!-- [Guide][guide] -->'); self.bad('missing named navigation')
    def test_escaped_link_is_not_navigation(self):
        self.change('[Guide][guide]', '\\[Guide]\\[guide]'); self.bad('missing named navigation')
    def test_missing_fragment_direct_failure(self):
        self.change('guide.md#target', 'guide.md#absent'); self.bad('missing target anchor')
    def test_anchor_in_code_does_not_exist(self):
        self.write('guide.md', '# Guide\n```html\n<a id="target"></a>\n```\n'); self.bad('missing target anchor')
    def test_directory_with_real_readme_is_valid_neighbor(self):
        self.write('guide-dir/README.md', '# Directory\n')
        self.write('extra.md', '[Guide](guide-dir/)')
        self.assertEqual(validate_document_links(self.root, 'extra.md')[1]['local'], 1)
    def test_valid_heading_and_unicode_fragment_neighbor(self):
        self.write('中文 指南.md', '# 中文标题\n')
        self.write('extra.md', '[中文](%E4%B8%AD%E6%96%87%20%E6%8C%87%E5%8D%97.md#%E4%B8%AD%E6%96%87%E6%A0%87%E9%A2%98)')
        self.assertEqual(validate_document_links(self.root, 'extra.md')[1]['local'], 1)
    def test_quoted_title_and_balanced_uri_neighbor(self):
        self.write('guide(v1).md', '# Guide\n')
        self.write('extra.md', '[Guide](guide(v1).md "Version one")')
        self.assertEqual(validate_document_links(self.root, 'extra.md')[1]['local'], 1)
    def test_escaped_parentheses_neighbor(self):
        self.write('guide(v1).md', '# Guide\n')
        self.write('extra.md', r'[Guide](guide\(v1\).md)')
        self.assertEqual(validate_document_links(self.root, 'extra.md')[1]['local'], 1)
    def test_collapsed_reference_neighbor(self):
        self.change('[Guide][guide]', '[Guide][]'); self.check()
    def test_shortcut_reference_neighbor(self):
        self.change('[Guide][guide]', '[Guide]'); self.check()
    def test_inline_instead_of_reference_neighbor(self):
        self.change('[Guide][guide]', '[Guide](guide.md#target)'); self.check()
    def test_reference_image_neighbor(self):
        self.change('![Brand](assets/cover.svg)', '![Brand][cover]\n\n[cover]: assets/cover.svg'); self.check()
    def test_undefined_reference_direct_failure(self):
        self.change('[Guide][guide]', '[Guide][undefined]'); self.bad('undefined reference')
    def test_badge_target_direct_failure(self):
        self.change('](#status)', '](guide.md#target)'); self.bad('badge destination')
    def test_unregistered_badge_url_direct_failure(self):
        self.change(self.badge_url, self.badge_url.replace('1%20adopted', '999%20adopted'))
        self.bad('unregistered README image or badge')
    def test_badge_count_must_match_source_collection(self):
        self.write('registry/standards.json', '[{"id":"STD-EXAMPLE-001","status":"adopted"},{"id":"STD-EXAMPLE-002","status":"adopted"}]')
        self.bad('source value')
    def test_badge_source_state_direct_failure(self):
        self.write('registry/standards.json', '[{"id":"STD-EXAMPLE-001","status":"draft"}]')
        self.bad('adopted document state')
    def test_duplicate_document_cannot_inflate_badge_count(self):
        self.write('registry/standards.json', '[{"id":"STD-EXAMPLE-001","status":"adopted"},{"id":"STD-EXAMPLE-001","status":"adopted"}]')
        self.bad('duplicate identities')
    def test_badge_alt_must_match_visible_claim(self):
        self.change('Documents: 1 adopted', 'Documents: 2 adopted')
        self.bad('alternative differs')
    def test_wrong_english_navigation_direct_failure(self):
        self.change('[Guide][guide]', '[Guide](README.md)', 'README.en.md'); self.bad('missing named navigation')
    def test_english_command_drift_direct_failure(self):
        self.change('python check.py', 'python skip.py', 'README.en.md'); self.bad('command contract')
    def test_english_reciprocal_link_missing(self):
        self.change('[Language](README.md)', 'Language', 'README.en.md'); self.bad('reciprocal')
    def test_named_html_link_neighbor(self):
        self.change('[Guide][guide]', '<a href="guide.md#target">Guide</a>'); self.check()
    def test_html_image_neighbor(self):
        self.change('![Brand](assets/cover.svg)', '<img src="assets/cover.svg" alt="Brand">'); self.check()
    def test_decorative_unlinked_image_neighbor(self):
        self.write('extra.md', '<img src="assets/cover.svg" alt="" role="presentation">')
        validate_document_links(self.root, 'extra.md')
    def test_decorative_linked_image_still_needs_name(self):
        self.write('extra.md', '<a href="guide.md"><img src="assets/cover.svg" alt="" role="presentation"></a>')
        with self.assertRaisesRegex(ValidationError, 'alternative'): validate_document_links(self.root, 'extra.md')
    def test_cover_cannot_claim_decoration_to_hide_missing_alt(self):
        self.change('![Brand](assets/cover.svg)', '<img src="assets/cover.svg" alt="" role="presentation">')
        self.bad('meaningful README asset')
    def test_unregistered_badge_fails(self):
        self.write('assets/extra.svg', SVG)
        self.change('# Example', '# Example\n\n![Passing](assets/extra.svg)')
        self.bad('unregistered README image or badge')
    def test_html_code_is_not_navigation(self):
        self.change('[Guide][guide]', '`<a href="guide.md#target">Guide</a>`'); self.bad('missing named navigation')
    def test_hidden_html_is_not_navigation(self):
        self.change('[Guide][guide]', '<a href="guide.md#target" hidden>Guide</a>'); self.bad('hidden HTML')
    def test_svg_title_missing_direct_failure(self):
        self.write('assets/cover.svg', SVG.replace('<title>Brand</title>', '')); self.bad('SVG title')
    def test_svg_corruption_direct_failure(self):
        self.write('assets/cover.svg', 'not an svg'); self.bad('invalid SVG')
    def test_decoded_parent_escape_direct_failure(self):
        self.write('extra.md', '[Outside](%2e%2e/secret.md)')
        with self.assertRaisesRegex(ValidationError, 'escapes repository'): validate_document_links(self.root, 'extra.md')
    def test_symlink_escape_direct_failure(self):
        make_symlink(self.root/'outside', self.root.parent, target_is_directory=True)
        self.write('extra.md', '[Outside](outside/secret.md)')
        with self.assertRaisesRegex(ValidationError, 'escapes repository'): validate_document_links(self.root, 'extra.md')
    def test_relative_parent_inside_root_valid_neighbor(self):
        self.write('sub/extra.md', '[Guide](../guide.md#target)')
        validate_document_links(self.root, 'sub/extra.md')
    def test_javascript_protocol_failure(self):
        self.write('extra.md', '[Action](javascript:alert(1))')
        with self.assertRaisesRegex(ValidationError, 'unsupported link protocol'): validate_document_links(self.root, 'extra.md')
    def test_external_url_is_not_falsely_fetched(self):
        self.write('extra.md', '[Reference](https://example.invalid/page)')
        self.assertEqual(validate_document_links(self.root, 'extra.md')[1]['external_not_fetched'], 1)
    def test_existing_file_query_is_not_offline_proof(self):
        with self.assertRaisesRegex(ValidationError, 'local query'): resolve_target(self.root, self.root/'README.md', 'guide.md?mode=other')


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name); self.addCleanup(self.tmp.cleanup)
        self.zh = '**版本：** 0.1\n\n### PGE-01 条款\n\n中文要求。\n'
        self.en = '**Source version:** 0.1\n\n### PGE-01 Clause\n\nEnglish requirement.\n'
        (self.root/'zh.md').write_text(self.zh, encoding='utf-8', newline='\n'); (self.root/'en.md').write_text(self.en, encoding='utf-8', newline='\n')
        self.row = {'document_id': 'STD-PG-005', 'source_version': '0.1', 'source_language': 'zh-Hans', 'target_language': 'en',
                    'authority': 'source-only', 'source_path': 'zh.md', 'target_path': 'en.md', 'source_sha256': digest(self.zh),
                    'target_sha256': digest(self.en), 'clause_ids': ['PGE-01'], 'coverage': 'full'}
    def check(self): return validate_translations(self.root, [self.row])
    def test_identity_only_positive(self):
        self.assertEqual(self.check()['result'], 'identity-verified')
        self.assertEqual(self.check()['clauses'], 1)
        self.assertIn('language labels', self.check()['scope'])
    def test_language_and_coverage_contracts_remain_required(self):
        for field,value in (('source_language','en'),('target_language','zh-Hans'),('coverage','partial')):
            with self.subTest(field=field),self.assertRaisesRegex(ValidationError,'authority/coverage'):
                validate_translations(self.root,[dict(self.row,**{field:value})])
    def test_source_change_same_version_stale(self):
        (self.root/'zh.md').write_text(self.zh+'新义务。', encoding='utf-8', newline='\n')
        with self.assertRaisesRegex(ValidationError, 'stale translation source'): self.check()
    def test_translation_change_stale(self):
        (self.root/'en.md').write_text(self.en+'New text.', encoding='utf-8', newline='\n')
        with self.assertRaisesRegex(ValidationError, 'stale translation target'): self.check()
    def test_missing_clause_after_digest_refresh_fails(self):
        text = self.en.replace('### PGE-01 Clause', '### Clause'); (self.root/'en.md').write_text(text, encoding='utf-8', newline='\n'); self.row['target_sha256'] = digest(text)
        with self.assertRaisesRegex(ValidationError, 'clause sequence'): self.check()
    def test_source_version_mismatch(self):
        self.row['source_version'] = '0.2'
        with self.assertRaisesRegex(ValidationError, 'version mismatch'): self.check()
    def test_duplicate_mapping_fails(self):
        with self.assertRaisesRegex(ValidationError, 'duplicate translation'): validate_translations(self.root, [self.row, copy.deepcopy(self.row)])
    def test_alias_source_is_not_translation(self):
        self.row['target_path'] = 'zh.md'
        with self.assertRaisesRegex(ValidationError, 'alias source'): self.check()
    def test_second_authority_fails(self):
        self.row['authority'] = 'translation'
        with self.assertRaisesRegex(ValidationError, 'authority/coverage'): self.check()
    def test_format_only_rebind_valid_neighbor(self):
        (self.root/'en.md').write_text(self.en+'\n', encoding='utf-8', newline='\n'); self.row['target_sha256'] = digest(self.en+'\n'); self.check()
    def test_identifier_in_code_does_not_fill_missing_clause(self):
        text = self.en.replace('### PGE-01 Clause', '```md\n### PGE-01 Clause\n```'); (self.root/'en.md').write_text(text, encoding='utf-8', newline='\n'); self.row['target_sha256'] = digest(text)
        with self.assertRaisesRegex(ValidationError, 'clause sequence'): self.check()


if __name__ == '__main__': unittest.main()
