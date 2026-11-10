"""Exercise the 0.2.0 to 0.2.1 transition without publishing to GitHub."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tests.test_release_bundle import fixture_source
from tests.test_release_publication import COMMIT, COMMITTED_AT, PREVIOUS, FakeGitHub
from tools.build_release_bundle import build, canonical
from tools.publish_release import PublishError, asset_names, publish, tag_object_id, tag_payload
from tools.verify_release_bundle import VerificationError, validate_release_config, verify_zip

CONFIG = {
    'schema': 'standards-release/1',
    'version': '0.2.1',
    'previous_version': '0.2.0',
    'notes_path': 'releases/v0.2.1.md',
}
NOTES = '# Standards 0.2.1\n\nSynthetic patch release.\n'


def patch_source():
    source = fixture_source()
    source['project.json'] = canonical({'name': 'Standards', 'version': '0.2.1'})
    source['releases/current.json'] = canonical(CONFIG)
    source[CONFIG['notes_path']] = NOTES.encode('utf-8')
    template = 'skills/ranzevor-standards/SKILL.md.in'
    source[template] = source[template].replace(b'version: "0.1.0"', b'version: "0.2.1"')
    return source


def published_predecessor():
    api = FakeGitHub(initial=True)
    payload = tag_payload('v0.2.0', PREVIOUS, '# Standards 0.2.0\n', COMMITTED_AT)
    ident = tag_object_id(payload)
    api.tag_objects[ident] = api.tag_object(payload)
    api.tags['v0.2.0'] = ident
    api.releases.append(api.release(1, 'v0.2.0', PREVIOUS, False, '# Standards 0.2.0\n'))
    return api


class PatchReleaseTests(unittest.TestCase):
    def test_patch_requires_the_exact_predecessor(self):
        self.assertEqual(validate_release_config(CONFIG, '0.2.1'), CONFIG)
        for previous in (None, '0.1.2', '0.2.1', '0.2.2', '0.2.00'):
            with self.subTest(previous=previous), self.assertRaises(VerificationError):
                validate_release_config({**CONFIG, 'previous_version': previous})
        with self.assertRaisesRegex(VerificationError, 'notes path'):
            validate_release_config({**CONFIG, 'notes_path': 'releases/v0.2.0.md'})

    def test_both_packages_use_patch_version_without_rewriting_normative_sources(self):
        source = patch_source()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'source'
            for name, raw in source.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            output = Path(temporary) / 'artifacts'
            report = build(root, output)
            self.assertEqual(report['version'], '0.2.1')
            self.assertEqual(report['documents'], 162)
            self.assertEqual({item.name for item in output.iterdir()}, set(asset_names('0.2.1')))
            for kind, prefix in (('source', 'Standards-v0.2.1/source/'),
                                 ('agent-skill', 'ranzevor-standards/references/')):
                with self.subTest(kind=kind):
                    archive = output / f'Standards-v0.2.1-{kind}.zip'
                    self.assertEqual(verify_zip(archive)['version'], '0.2.1')
                    with zipfile.ZipFile(archive) as bundle:
                        self.assertEqual(json.loads(bundle.read(prefix + 'releases/current.json')), CONFIG)
                        self.assertEqual(bundle.read(prefix + 'registry/standards.json'),
                                         source['registry/standards.json'])
                        for name, raw in source.items():
                            if name.startswith('standards/'):
                                self.assertEqual(bundle.read(prefix + name), raw)
                        if kind == 'agent-skill':
                            self.assertIn(b'version: "0.2.1"', bundle.read('ranzevor-standards/SKILL.md'))

    def test_publication_preserves_predecessor_and_reuses_the_same_patch(self):
        api = published_predecessor()
        previous = copy.deepcopy(api.releases[0])
        tag = api.tags['v0.2.0']
        assets = {name: ('synthetic ' + name).encode('utf-8') for name in asset_names('0.2.1')}
        result = publish(api, CONFIG, assets, COMMIT, NOTES)
        self.assertEqual(result['status'], 'published-and-verified')
        self.assertEqual(result['tag']['name'], 'v0.2.1')
        self.assertEqual(result['tag']['peeled_commit'], COMMIT)
        self.assertEqual(api.releases[0], previous)
        self.assertEqual(api.tags['v0.2.0'], tag)
        release = next(item for item in api.releases if item['tag_name'] == 'v0.2.1')
        self.assertFalse(release['draft'])
        self.assertEqual(release['body'], NOTES)
        self.assertEqual({item['name'] for item in api.assets.values()
                          if item['release_id'] == release['id']}, set(assets))
        api.mutations.clear()
        self.assertTrue(publish(api, CONFIG, assets, COMMIT, NOTES)['reused'])
        self.assertEqual(api.mutations, [])

    def test_missing_or_unpublished_predecessor_rejects_before_mutation(self):
        assets = {name: b'synthetic asset' for name in asset_names('0.2.1')}
        for state in ('missing', 'draft'):
            with self.subTest(state=state):
                api = published_predecessor()
                if state == 'missing':
                    api.releases.clear()
                else:
                    api.releases[0]['draft'] = True
                    api.releases[0]['published_at'] = None
                with self.assertRaises(PublishError):
                    publish(api, CONFIG, assets, COMMIT, NOTES)
                self.assertEqual(api.mutations, [])
                self.assertNotIn('v0.2.1', api.tags)


if __name__ == '__main__':
    unittest.main()
