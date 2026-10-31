"""Release version separation and publication recovery use actual bytes and a fake GitHub target."""
import copy
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import call, patch
import urllib.request

from tools.publish_release import (
    APIError, API_PREFIX, GitHubAPI, PublishError, SafeRedirect, asset_names, publish,
    ensure_tag, tag_commit, tag_object_bytes, tag_object_id, tag_payload,
)

COMMIT = 'a' * 40
PREVIOUS = 'b' * 40
COMMITTED_AT = '2026-10-28T12:34:56Z'
CONFIG = {'schema': 'standards-release/1', 'version': '0.1.1',
          'previous_version': '0.1.0', 'notes_path': 'releases/v0.1.1.md'}
NOTES = '# Standards v0.1.1\n\nSynthetic test notes.\n'
ASSETS = {name: ('synthetic ' + name).encode() for name in asset_names('0.1.1')}
INITIAL_CONFIG = {'schema': 'standards-release/1', 'version': '0.1.0',
                  'previous_version': None, 'notes_path': 'releases/v0.1.0.md'}
INITIAL_NOTES = '# Standards v0.1.0\n\nSynthetic initial release notes.\n'
INITIAL_ASSETS = {name: ('synthetic ' + name).encode() for name in asset_names('0.1.0')}


class FakeGitHub:
    def __init__(self, initial=False):
        self.main = COMMIT
        self.tags = {} if initial else {'v0.1.0': PREVIOUS}
        self.tag_objects = {}
        self.releases = [] if initial else [self.release(1, 'v0.1.0', PREVIOUS, False, 'Previous release')]
        self.assets = {}
        self.bytes = {}
        self.mutations = []
        self.requests = []
        self.downloads = []
        self.next_id = 100
        self.fail_after = set()
        self.fail_before = set()
        self.tag_payloads = []
        self.main_reads = 0
        self.move_main_before_publish = False
        self.comparison_status = 'ahead'

    def release(self, ident, tag, commit, draft, body):
        return {'id': ident, 'tag_name': tag, 'target_commitish': commit,
                'draft': draft, 'prerelease': False, 'name': 'Standards ' + tag,
                'body': body, 'published_at': None if draft else '2026-10-28T00:00:00Z',
                'upload_url': f'https://uploads.github.com{API_PREFIX}/releases/{ident}/assets{{?name,label}}',
                'html_url': 'https://github.com/ranzevor/Standards/releases/tag/' + tag}

    def seed_current(self, draft=True, version='0.1.1', notes=NOTES):
        tag = 'v' + version
        payload = tag_payload(tag, COMMIT, notes, COMMITTED_AT)
        object_id = tag_object_id(payload)
        self.tag_objects[object_id] = self.tag_object(payload)
        self.tags[tag] = object_id
        current = self.release(2, tag, COMMIT, draft, notes)
        self.releases.append(current)
        return current

    def tag_object(self, payload):
        return {'sha': tag_object_id(payload), 'tag': payload['tag'],
                'message': payload['message'], 'tagger': copy.deepcopy(payload['tagger']),
                'object': {'type': payload['type'], 'sha': payload['object']},
                'verification': {'verified': False, 'reason': 'unsigned', 'signature': None}}

    def lost_response(self, operation):
        if operation in self.fail_after:
            self.fail_after.remove(operation)
            raise APIError(None, 'synthetic lost response')

    def request(self, method, suffix, payload=None, missing=False):
        path = suffix.split('?', 1)[0]
        self.requests.append((method, path))
        if method != 'GET':
            self.mutations.append((method, path))
        if method == 'GET' and path == '/releases':
            return copy.deepcopy(self.releases if 'page=1' in suffix else [])
        if method == 'GET' and path == '/git/ref/heads/main':
            self.main_reads += 1
            if self.move_main_before_publish and self.main_reads > 1:
                self.main = 'c' * 40
            return {'object': {'sha': self.main, 'type': 'commit'}}
        if method == 'GET' and path.startswith('/git/ref/tags/'):
            tag = path.rsplit('/', 1)[1]
            if tag not in self.tags:
                if missing:
                    return None
                raise APIError(404, 'missing tag')
            return {'object': {'sha': self.tags[tag],
                               'type': 'tag' if self.tags[tag] in self.tag_objects else 'commit'}}
        if method == 'GET' and path.startswith('/git/commits/'):
            return {'sha': path.rsplit('/', 1)[1], 'committer': {'date': COMMITTED_AT}}
        if method == 'GET' and path.startswith('/git/tags/'):
            object_id = path.rsplit('/', 1)[1]
            if object_id not in self.tag_objects:
                if missing:
                    return None
                raise APIError(404, 'missing tag object')
            return copy.deepcopy(self.tag_objects[object_id])
        if method == 'POST' and path == '/git/tags':
            self.tag_payloads.append(copy.deepcopy(payload))
            if 'tag-object' in self.fail_before:
                self.fail_before.remove('tag-object')
                raise APIError(None, 'synthetic unknown outcome before creation')
            record = self.tag_object(payload)
            self.tag_objects[record['sha']] = record
            self.lost_response('tag-object')
            return copy.deepcopy(record)
        if method == 'GET' and path.startswith('/compare/'):
            return {'status': self.comparison_status}
        if method == 'POST' and path == '/git/refs':
            self.tags[payload['ref'].split('/')[-1]] = payload['sha']
            self.lost_response('tag')
            return {'object': {'sha': payload['sha'], 'type': 'commit'}}
        if method == 'POST' and path == '/releases':
            current = self.release(2, payload['tag_name'], payload['target_commitish'],
                                   payload['draft'], payload['body'])
            self.releases.append(current)
            self.lost_response('release')
            return copy.deepcopy(current)
        if path.startswith('/releases/') and path.endswith('/assets') and method == 'GET':
            release_id = int(path.split('/')[2])
            return copy.deepcopy([a for a in self.assets.values() if a['release_id'] == release_id])
        if method == 'DELETE' and path.startswith('/releases/assets/'):
            ident = int(path.rsplit('/', 1)[1])
            self.assets.pop(ident)
            self.bytes.pop(ident, None)
            return None
        if path.startswith('/releases/') and path.rsplit('/', 1)[1].isdigit():
            current = next(r for r in self.releases if r['id'] == int(path.rsplit('/', 1)[1]))
            if method == 'PATCH':
                current['draft'] = payload['draft']
                current['published_at'] = '2026-10-28T00:00:00Z'
                self.lost_response('publish')
            return copy.deepcopy(current)
        raise AssertionError((method, suffix, payload))

    def upload(self, release, name, raw):
        self.mutations.append(('UPLOAD', name))
        require_missing = [a for a in self.assets.values()
                           if a['release_id'] == release['id'] and a['name'] == name]
        if require_missing:
            raise APIError(422, 'duplicate upload')
        self.next_id += 1
        ident = self.next_id
        asset = {'id': ident, 'release_id': release['id'], 'name': name, 'state': 'uploaded',
                 'size': len(raw), 'digest': 'sha256:' + hashlib.sha256(raw).hexdigest()}
        self.assets[ident] = asset
        self.bytes[ident] = raw
        self.lost_response('upload')
        return copy.deepcopy(asset)

    def download(self, asset):
        self.downloads.append(asset['id'])
        return self.bytes[asset['id']]


class DelayedTagGitHub(FakeGitHub):
    def __init__(self, operation, responses):
        super().__init__()
        self.operation = operation
        self.responses = list(responses)
        self.confirmation_reads = 0
        self.created = False

    def request(self, method, suffix, payload=None, missing=False):
        target = '/git/tags/' if self.operation == 'tag-object' else '/git/ref/tags/'
        if method == 'GET' and suffix.startswith(target) and self.created and self.responses:
            self.requests.append((method, suffix))
            self.confirmation_reads += 1
            response = self.responses.pop(0)
            if isinstance(response, APIError):
                raise response
            if response is None:
                if missing:
                    return None
                raise APIError(404, 'synthetic delayed tag readback')
            return response
        try:
            return super().request(method, suffix, payload, missing)
        finally:
            if method == 'POST' and suffix == ('/git/tags' if self.operation == 'tag-object' else '/git/refs'):
                self.created = True


class TagReadbackRecoveryTests(unittest.TestCase):
    def setUp(self):
        sleeper = patch('time.sleep')
        self.sleeper = sleeper.start()
        self.addCleanup(sleeper.stop)

    def test_delayed_created_object_and_ref_are_confirmed_without_repeating_posts(self):
        for operation in ('tag-object', 'tag'):
            for lost_response in (False, True):
                with self.subTest(operation=operation, lost_response=lost_response):
                    api = DelayedTagGitHub(operation, [None, None])
                    if lost_response:
                        api.fail_after.add(operation)
                    result = publish(api, CONFIG, ASSETS, COMMIT, NOTES)
                    self.assertEqual(result['status'], 'published-and-verified')
                    self.assertEqual(api.confirmation_reads, 2)
                    self.assertEqual(api.mutations.count(('POST', '/git/tags')), 1)
                    self.assertEqual(api.mutations.count(('POST', '/git/refs')), 1)
                    self.assertEqual(len(api.tag_objects), 1)

    def test_transient_read_failure_recovers_but_permission_failure_stops_immediately(self):
        for status in (None, 408, 429, 500, 502, 503, 504, 401, 403):
            with self.subTest(status=status):
                api = DelayedTagGitHub('tag', [APIError(status, 'synthetic read failure')])
                self.sleeper.reset_mock()
                if status in (401, 403):
                    with self.assertRaises(APIError) as caught:
                        publish(api, CONFIG, ASSETS, COMMIT, NOTES)
                    self.assertEqual(caught.exception.status, status)
                    self.assertEqual(api.confirmation_reads, 1)
                    self.sleeper.assert_not_called()
                    self.assertNotIn(('POST', '/releases'), api.mutations)
                else:
                    self.assertEqual(publish(api, CONFIG, ASSETS, COMMIT, NOTES)['status'],
                                     'published-and-verified')
                    self.assertEqual(self.sleeper.call_count, 1)

    def test_write_permission_error_is_not_reclassified_as_incomplete_confirmation(self):
        for denied_path in ('/git/tags', '/git/refs'):
            for status in (401, 403):
                with self.subTest(denied_path=denied_path, status=status):
                    api = FakeGitHub()
                    request = api.request
                    self.sleeper.reset_mock()

                    def deny_write(method, suffix, payload=None, missing=False):
                        if method == 'POST' and suffix == denied_path:
                            raise APIError(status, 'synthetic write permission failure')
                        return request(method, suffix, payload, missing)

                    with patch.object(api, 'request', side_effect=deny_write):
                        with self.assertRaises(APIError) as caught:
                            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
                    self.assertEqual(caught.exception.status, status)
                    self.sleeper.assert_not_called()
                    self.assertNotIn(('POST', '/releases'), api.mutations)

    def test_confirmation_exhaustion_leaves_exact_objects_recoverable_without_publication(self):
        for operation in ('tag-object', 'tag'):
            with self.subTest(operation=operation):
                api = DelayedTagGitHub(operation, [None] * 4)
                self.sleeper.reset_mock()
                with self.assertRaisesRegex(APIError, 'confirmation incomplete'):
                    publish(api, CONFIG, ASSETS, COMMIT, NOTES)
                self.assertEqual(api.confirmation_reads, 4)
                self.assertEqual(self.sleeper.call_args_list, [call(1), call(2), call(4)])
                self.assertNotIn(('POST', '/releases'), api.mutations)
                self.assertEqual(len(api.tag_objects), 1)
                if operation == 'tag-object':
                    self.assertNotIn('v0.1.1', api.tags)
                api.mutations.clear()
                result = publish(api, CONFIG, ASSETS, COMMIT, NOTES)
                self.assertEqual(result['status'], 'published-and-verified')
                self.assertNotIn(('POST', '/git/tags'), api.mutations)
                if operation == 'tag':
                    self.assertNotIn(('POST', '/git/refs'), api.mutations)

    def test_visible_conflicting_ref_is_rejected_without_waiting_for_a_different_answer(self):
        conflicting = {'object': {'type': 'tag', 'sha': 'c' * 40}}
        api = DelayedTagGitHub('tag', [conflicting])
        with self.assertRaisesRegex(PublishError, 'tag ref differs'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.sleeper.assert_not_called()
        self.assertEqual(api.confirmation_reads, 1)
        self.assertNotIn(('POST', '/releases'), api.mutations)
        self.assertFalse(any(method in ('PATCH', 'DELETE') for method, _ in api.mutations))


class PublicationRecoveryTests(unittest.TestCase):
    def test_initial_publication_verifies_assets_and_reuses_same_release(self):
        api = FakeGitHub(initial=True)
        first = publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
        self.assertEqual(first['status'], 'published-and-verified')
        self.assertFalse(first['reused'])
        self.assertEqual(first['tag']['name'], 'v0.1.0')
        self.assertEqual(first['tag']['kind'], 'annotated')
        self.assertEqual(len(api.releases), 1)
        self.assertEqual(set(a['name'] for a in api.assets.values()), set(INITIAL_ASSETS))
        self.assertTrue(set(api.assets) <= set(api.downloads))
        self.assertFalse(any(path.startswith('/compare/') for _, path in api.requests))
        api.mutations.clear()
        api.downloads.clear()
        api.main = 'c' * 40
        second = publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES,
                         verify_only=True)
        self.assertTrue(second['reused'])
        self.assertEqual(api.mutations, [])
        self.assertEqual(set(api.assets), set(api.downloads))

    def test_initial_lost_responses_are_reconciled_without_duplicate_objects(self):
        for operation in ('tag-object', 'tag', 'release', 'upload', 'publish'):
            with self.subTest(operation=operation):
                api = FakeGitHub(initial=True)
                api.fail_after.add(operation)
                result = publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
                self.assertEqual(result['status'], 'published-and-verified')
                self.assertEqual((len(api.releases), len(api.assets), len(api.tag_objects)),
                                 (1, 4, 1))

    def test_initial_release_rejects_tag_conflict_and_changed_main(self):
        for mutation in ('tag-conflict', 'main-drift', 'other-release'):
            with self.subTest(mutation=mutation):
                api = FakeGitHub(initial=True)
                if mutation == 'tag-conflict':api.tags['v0.1.0'] = 'c' * 40
                elif mutation == 'main-drift':api.main = 'c' * 40
                else:api.releases.append(api.release(1, 'v0.1.1', PREVIOUS, False, 'Existing'))
                with self.assertRaises(PublishError):
                    publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
                self.assertEqual(api.mutations, [])

    def test_initial_release_preserves_an_unpublished_future_draft(self):
        api = FakeGitHub(initial=True)
        draft = api.release(7, 'v0.1.1', PREVIOUS, True, 'Future draft')
        api.releases.append(copy.deepcopy(draft))
        result = publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
        self.assertEqual(result['status'], 'published-and-verified')
        self.assertEqual(next(item for item in api.releases if item['id'] == 7), draft)
        self.assertNotIn(('PATCH', '/releases/7'), api.mutations)
        self.assertNotIn(('DELETE', '/releases/7'), api.mutations)

    def test_initial_release_rechecks_publication_order_after_upload_and_readback(self):
        class ConcurrentRelease(FakeGitHub):
            def __init__(self, stage, draft):
                super().__init__(initial=True)
                self.stage = stage
                self.other = self.release(7, 'v0.1.1', PREVIOUS, draft, 'Concurrent release')
                self.injected = False

            def inject(self):
                if not self.injected:
                    self.releases.append(copy.deepcopy(self.other))
                    self.injected = True

            def upload(self, release, name, raw):
                result = super().upload(release, name, raw)
                if self.stage == 'upload':self.inject()
                return result

            def download(self, asset):
                result = super().download(asset)
                if self.stage == 'readback' and len(self.downloads) > len(INITIAL_ASSETS):
                    self.inject()
                return result

        for stage in ('upload', 'readback'):
            for draft in (False, True):
                with self.subTest(stage=stage, other_is_draft=draft):
                    api = ConcurrentRelease(stage, draft)
                    if draft:
                        result = publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
                        self.assertEqual(result['status'], 'published-and-verified')
                    else:
                        with self.assertRaisesRegex(PublishError, 'another published release'):
                            publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
                        current = next(item for item in api.releases if item['tag_name'] == 'v0.1.0')
                        self.assertTrue(current['draft'])
                        self.assertNotIn(('PATCH', '/releases/2'), api.mutations)
                    self.assertTrue(api.injected)
                    self.assertEqual(next(item for item in api.releases if item['id'] == 7), api.other)
                    self.assertNotIn(('PATCH', '/releases/7'), api.mutations)
                    self.assertNotIn(('DELETE', '/releases/7'), api.mutations)
                    self.assertEqual(len(api.assets), 4)

    def test_initial_draft_reuses_matching_bytes_and_rejects_different_bytes(self):
        for matching in (True, False):
            with self.subTest(matching=matching):
                api = FakeGitHub(initial=True)
                release = api.seed_current(version='0.1.0', notes=INITIAL_NOTES)
                name = next(iter(INITIAL_ASSETS))
                raw = INITIAL_ASSETS[name] if matching else b'preserve different bytes'
                api.upload(release, name, raw)
                api.mutations.clear()
                if matching:
                    publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
                    self.assertNotIn(('UPLOAD', name), api.mutations)
                    self.assertEqual(len(api.assets), 4)
                else:
                    with self.assertRaises(PublishError):
                        publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
                    self.assertEqual(api.mutations, [])
                    self.assertIn(raw, api.bytes.values())

    def test_initial_main_drift_after_upload_keeps_draft_unpublished(self):
        api = FakeGitHub(initial=True)
        api.move_main_before_publish = True
        with self.assertRaisesRegex(PublishError, 'main changed before publication'):
            publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
        self.assertEqual(len(api.releases), 1)
        self.assertTrue(api.releases[0]['draft'])
        self.assertNotIn(('PATCH', '/releases/2'), api.mutations)

    def test_initial_published_asset_tampering_is_rejected_without_mutation(self):
        api = FakeGitHub(initial=True)
        publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
        ident = next(iter(api.assets))
        api.bytes[ident] = b'!' + api.bytes[ident][1:]
        api.mutations.clear()
        with self.assertRaisesRegex(PublishError, 'downloaded bytes differ'):
            publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
        self.assertEqual(api.mutations, [])

    def test_subsequent_release_still_requires_published_predecessor_and_ancestry(self):
        for mutation in ('missing-release', 'draft', 'prerelease', 'missing-tag', 'not-ahead'):
            with self.subTest(mutation=mutation):
                api = FakeGitHub()
                if mutation == 'missing-release':api.releases.clear()
                elif mutation == 'draft':api.releases[0]['draft'] = True
                elif mutation == 'prerelease':api.releases[0]['prerelease'] = True
                elif mutation == 'missing-tag':api.tags.clear()
                else:api.comparison_status = 'identical'
                with self.assertRaises(PublishError):
                    publish(api, CONFIG, ASSETS, COMMIT, NOTES)
                self.assertEqual(api.mutations, [])

    def test_tag_object_encoding_matches_real_git_and_peels_to_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = dict(os.environ, GIT_AUTHOR_DATE=COMMITTED_AT,
                               GIT_COMMITTER_DATE=COMMITTED_AT)
            for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE',
                         'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_PREFIX'):
                environment.pop(name, None)
            def git(*args, data=None):
                return subprocess.run(
                    ['git', '-C', str(root), '-c', 'user.name=Synthetic Test',
                     '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgSign=false',
                     '-c', 'core.hooksPath=/dev/null', *args],
                    input=data, capture_output=True, check=True, env=environment, timeout=30).stdout
            git('init', '-q', '--object-format=sha1')
            git('commit', '--allow-empty', '-qm', 'Synthetic tag fixture')
            commit = git('rev-parse', 'HEAD').decode().strip()
            payload = tag_payload('v0.1.1', commit, NOTES, COMMITTED_AT)
            raw = tag_object_bytes(payload)
            actual = git('mktag', data=raw).decode().strip()
            self.assertEqual(actual, tag_object_id(payload))
            self.assertEqual(git('cat-file', 'tag', actual), raw)
            git('update-ref', 'refs/tags/v0.1.1', actual)
            self.assertEqual(git('rev-parse', 'v0.1.1^{commit}').decode().strip(), commit)
            self.assertIn(b'Signature policy: unsigned\n', raw)
            self.assertIn(b'<standards-release@automation.invalid>', raw)

    def test_tag_identity_is_deterministic_and_binds_name_message_target_and_time(self):
        original = tag_payload('v0.1.1', COMMIT, NOTES, COMMITTED_AT)
        equivalent = tag_payload('v0.1.1', COMMIT, NOTES, '2026-10-28T20:34:56+08:00')
        self.assertEqual(original, equivalent)
        original_id = tag_object_id(original)
        for payload in (tag_payload('v0.1.2', COMMIT, NOTES, COMMITTED_AT),
                        tag_payload('v0.1.1', PREVIOUS, NOTES, COMMITTED_AT),
                        tag_payload('v0.1.1', COMMIT, NOTES + '变更说明。\n', COMMITTED_AT),
                        tag_payload('v0.1.1', COMMIT, NOTES, '2026-10-28T12:34:57Z')):
            self.assertNotEqual(tag_object_id(payload), original_id)

    def test_unknown_tag_object_creation_stops_before_public_ref_and_reuses_same_identity(self):
        api = FakeGitHub()
        api.fail_before.add('tag-object')
        with self.assertRaises(APIError):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.mutations, [('POST', '/git/tags')])
        self.assertNotIn('v0.1.1', api.tags)
        publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.tag_payloads[0], api.tag_payloads[1])
        self.assertEqual(len(api.tag_objects), 1)

    def test_existing_unreferenced_object_is_reused_without_another_object_create(self):
        api = FakeGitHub()
        payload = tag_payload('v0.1.1', COMMIT, NOTES, COMMITTED_AT)
        object_id = tag_object_id(payload)
        api.tag_objects[object_id] = api.tag_object(payload)
        receipt = ensure_tag(api, 'v0.1.1', COMMIT, NOTES)
        self.assertEqual(receipt['object_sha'], object_id)
        self.assertNotIn(('POST', '/git/tags'), api.mutations)
        self.assertEqual(tag_commit(api, 'v0.1.1'), COMMIT)

    def test_mismatched_tag_object_readback_is_rejected_before_ref_creation(self):
        for field, value in (('tag', 'v0.1.2'), ('message', 'different message')):
            with self.subTest(field=field):
                api = FakeGitHub()
                payload = tag_payload('v0.1.1', COMMIT, NOTES, COMMITTED_AT)
                record = api.tag_object(payload)
                record[field] = value
                api.tag_objects[record['sha']] = record
                with self.assertRaisesRegex(PublishError, 'immutable identity'):
                    ensure_tag(api, 'v0.1.1', COMMIT, NOTES)
                self.assertEqual(api.mutations, [])
                self.assertNotIn('v0.1.1', api.tags)

    def test_unpublished_lightweight_tag_is_not_replaced(self):
        api = FakeGitHub()
        api.tags['v0.1.1'] = COMMIT
        with self.assertRaisesRegex(PublishError, 'lightweight tag'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.mutations, [])
        self.assertEqual(api.tags['v0.1.1'], COMMIT)

    def test_published_lightweight_tag_is_rejected_without_replacement(self):
        api = FakeGitHub()
        release = api.seed_current(draft=False)
        api.tags['v0.1.1'] = COMMIT
        for name, raw in ASSETS.items():
            api.upload(release, name, raw)
        api.mutations.clear()
        with self.assertRaisesRegex(PublishError, 'published annotated tag differs'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.mutations, [])
        self.assertEqual(api.tags['v0.1.1'], COMMIT)

    def test_published_tag_rechecks_annotation_tagger_date_and_source_identity(self):
        for config, assets, notes in ((INITIAL_CONFIG, INITIAL_ASSETS, INITIAL_NOTES),
                                     (CONFIG, ASSETS, NOTES)):
            tag = 'v' + config['version']
            for field in ('message', 'tagger-name', 'tagger-email', 'tagger-date', 'tag', 'object'):
                with self.subTest(version=config['version'], field=field):
                    api = FakeGitHub(initial=config['previous_version'] is None)
                    release = api.seed_current(draft=False, version=config['version'], notes=notes)
                    for name, raw in assets.items():api.upload(release, name, raw)
                    payload = tag_payload(tag, COMMIT, notes, COMMITTED_AT)
                    if field == 'message':payload['message'] = 'Changed release notes digest\n'
                    elif field == 'tag':payload['tag'] = 'v0.1.99'
                    elif field == 'object':payload['object'] = PREVIOUS
                    else:
                        key = field.removeprefix('tagger-')
                        payload['tagger'][key] = {'name': 'Other Publisher',
                                                  'email': 'other@example.invalid',
                                                  'date': '2026-10-28T12:34:57Z'}[key]
                    changed_id = tag_object_id(payload)
                    api.tag_objects[changed_id] = api.tag_object(payload)
                    api.tags[tag] = changed_id
                    api.mutations.clear()
                    api.downloads.clear()
                    with self.assertRaises(PublishError):
                        publish(api, config, assets, COMMIT, notes, verify_only=True)
                    self.assertEqual(api.mutations, [])
                    self.assertEqual(api.downloads, [])
                    self.assertEqual(api.tags[tag], changed_id)

    def test_published_tag_readback_must_match_all_expected_fields(self):
        for field in ('message', 'tagger-name', 'tagger-email', 'tagger-date', 'signature'):
            with self.subTest(field=field):
                api = FakeGitHub(initial=True)
                release = api.seed_current(draft=False, version='0.1.0', notes=INITIAL_NOTES)
                for name, raw in INITIAL_ASSETS.items():api.upload(release, name, raw)
                record = api.tag_objects[api.tags['v0.1.0']]
                if field == 'message':record['message'] = 'Different annotation'
                elif field == 'signature':record['verification']['signature'] = 'Unexpected signature'
                else:record['tagger'][field.removeprefix('tagger-')] = 'different'
                api.mutations.clear()
                with self.assertRaisesRegex(PublishError, 'immutable identity|unsigned object'):
                    publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
                self.assertEqual(api.mutations, [])

    def test_published_tag_swap_during_asset_readback_is_rejected(self):
        class SwapDuringDownload(FakeGitHub):
            def download(self, asset):
                raw = super().download(asset)
                payload = tag_payload('v0.1.0', COMMIT, 'Changed annotation', COMMITTED_AT)
                object_id = tag_object_id(payload)
                self.tag_objects[object_id] = self.tag_object(payload)
                self.tags['v0.1.0'] = object_id
                return raw

        api = SwapDuringDownload(initial=True)
        release = api.seed_current(draft=False, version='0.1.0', notes=INITIAL_NOTES)
        for name, raw in INITIAL_ASSETS.items():api.upload(release, name, raw)
        api.mutations.clear()
        with self.assertRaisesRegex(PublishError, 'published annotated tag differs'):
            publish(api, INITIAL_CONFIG, INITIAL_ASSETS, COMMIT, INITIAL_NOTES)
        self.assertEqual(api.mutations, [])
        self.assertFalse(api.releases[0]['draft'])

    def test_different_annotated_object_at_same_commit_is_never_moved(self):
        api = FakeGitHub()
        payload = tag_payload('v0.1.1', COMMIT, 'Other annotation', COMMITTED_AT)
        object_id = tag_object_id(payload)
        api.tag_objects[object_id] = api.tag_object(payload)
        api.tags['v0.1.1'] = object_id
        with self.assertRaisesRegex(PublishError, 'annotated tag differs'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.mutations, [])
        self.assertEqual(api.tags['v0.1.1'], object_id)

    def test_publish_reads_actual_bytes_and_repeated_run_has_no_mutations(self):
        api = FakeGitHub()
        first = publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(first['status'], 'published-and-verified')
        self.assertFalse(first['reused'])
        self.assertEqual(first['tag']['kind'], 'annotated')
        self.assertEqual(first['tag']['peeled_commit'], COMMIT)
        self.assertEqual(first['tag']['signature'], 'unsigned')
        self.assertNotEqual(first['tag']['object_sha'], COMMIT)
        self.assertEqual(api.tags['v0.1.1'], first['tag']['object_sha'])
        self.assertEqual(set(a['name'] for a in api.assets.values()), set(ASSETS))
        api.mutations.clear()
        second = publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertTrue(second['reused'])
        self.assertEqual(api.mutations, [])

    def test_same_commit_tag_swap_cannot_redefine_the_intended_identity(self):
        class ConcurrentTagSwap(FakeGitHub):
            def __init__(self, stage):
                super().__init__()
                self.stage = stage
                self.swapped = False
                self.original = tag_object_id(tag_payload('v0.1.1', COMMIT, NOTES, COMMITTED_AT))
                other = tag_payload('v0.1.1', COMMIT, 'Unreviewed annotation', COMMITTED_AT)
                self.alternative = tag_object_id(other)
                self.tag_objects[self.alternative] = self.tag_object(other)

            def request(self, method, suffix, payload=None, missing=False):
                result = super().request(method, suffix, payload, missing)
                if (self.stage == 'after-ref-check' and not self.swapped and method == 'GET'
                        and suffix == '/git/tags/' + self.original
                        and self.tags.get('v0.1.1') == self.original):
                    self.tags['v0.1.1'] = self.alternative
                    self.swapped = True
                return result

            def upload(self, release, name, raw):
                result = super().upload(release, name, raw)
                if self.stage == 'during-upload' and not self.swapped:
                    self.tags['v0.1.1'] = self.alternative
                    self.swapped = True
                return result

        for stage in ('after-ref-check', 'during-upload'):
            with self.subTest(stage=stage):
                api = ConcurrentTagSwap(stage)
                with self.assertRaisesRegex(PublishError, 'tag changed before'):
                    publish(api, CONFIG, ASSETS, COMMIT, NOTES)
                self.assertTrue(api.swapped)
                self.assertEqual(api.tags['v0.1.1'], api.alternative)
                self.assertNotIn(('PATCH', '/releases/2'), api.mutations)
                self.assertFalse(any(r['tag_name'] == 'v0.1.1' and r['draft'] is False
                                     for r in api.releases))

    def test_lost_response_after_each_mutation_is_reconciled(self):
        for operation in ('tag-object', 'tag', 'release', 'upload', 'publish'):
            with self.subTest(operation=operation):
                api = FakeGitHub()
                api.fail_after.add(operation)
                self.assertEqual(publish(api, CONFIG, ASSETS, COMMIT, NOTES)['status'],
                                 'published-and-verified')
                self.assertEqual(len(api.releases), 2)
                self.assertEqual(len(api.assets), 4)
                self.assertEqual(len(api.tag_objects), 1)

    def test_tag_conflict_is_never_overwritten(self):
        api = FakeGitHub()
        api.tags['v0.1.1'] = 'c' * 40
        with self.assertRaisesRegex(PublishError, 'tag identity conflict'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.mutations, [])
        self.assertEqual(api.tags['v0.1.1'], 'c' * 40)

    def test_main_drift_blocks_before_mutation(self):
        api = FakeGitHub()
        api.main = 'c' * 40
        with self.assertRaisesRegex(PublishError, 'main changed'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.mutations, [])

    def test_main_drift_after_upload_preserves_unpublished_draft(self):
        api = FakeGitHub()
        api.move_main_before_publish = True
        with self.assertRaisesRegex(PublishError, 'main changed before publication'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertTrue(api.releases[-1]['draft'])
        self.assertNotIn(('PATCH', '/releases/2'), api.mutations)

    def test_partial_draft_reuses_identical_existing_asset(self):
        api = FakeGitHub()
        release = api.seed_current()
        name = next(iter(ASSETS))
        api.upload(release, name, ASSETS[name])
        api.mutations.clear()
        publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertNotIn(('UPLOAD', name), api.mutations)
        self.assertEqual(len(api.assets), 4)

    def test_different_existing_draft_asset_blocks_without_replacement(self):
        api = FakeGitHub()
        release = api.seed_current()
        name = next(iter(ASSETS))
        api.upload(release, name, b'wrong bytes')
        api.mutations.clear()
        with self.assertRaises(PublishError):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.mutations, [])
        self.assertIn(b'wrong bytes', api.bytes.values())

    def test_empty_starter_upload_can_be_recovered_only_on_draft(self):
        api = FakeGitHub()
        release = api.seed_current()
        name = next(iter(ASSETS))
        existing = api.upload(release, name, b'')
        api.assets[existing['id']]['state'] = 'starter'
        publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertIn(('DELETE', '/releases/assets/' + str(existing['id'])), api.mutations)
        self.assertNotIn(existing['id'], api.assets)

    def test_published_missing_asset_blocks_without_mutation(self):
        api = FakeGitHub()
        api.seed_current(draft=False)
        with self.assertRaisesRegex(PublishError, 'asset set differs'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.mutations, [])

    def test_published_byte_tampering_blocks_without_mutation(self):
        api = FakeGitHub()
        publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        ident = next(iter(api.assets))
        raw = api.bytes[ident]
        api.bytes[ident] = b'!' + raw[1:]
        api.mutations.clear()
        with self.assertRaisesRegex(PublishError, 'downloaded bytes differ'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.mutations, [])

    def test_unexpected_asset_is_not_deleted(self):
        api = FakeGitHub()
        release = api.seed_current()
        api.upload(release, 'unexpected.txt', b'preserve')
        api.mutations.clear()
        with self.assertRaisesRegex(PublishError, 'unexpected assets'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        self.assertEqual(api.mutations, [])

    def test_verify_mode_does_not_create_a_release(self):
        api = FakeGitHub()
        with self.assertRaisesRegex(PublishError, 'not published'):
            publish(api, CONFIG, ASSETS, COMMIT, NOTES, verify_only=True)
        self.assertEqual(api.mutations, [])

    def test_old_published_release_can_be_verified_after_main_advances(self):
        api = FakeGitHub()
        publish(api, CONFIG, ASSETS, COMMIT, NOTES)
        api.main = 'c' * 40
        api.mutations.clear()
        self.assertTrue(publish(api, CONFIG, ASSETS, COMMIT, NOTES, verify_only=True)['reused'])
        self.assertEqual(api.mutations, [])

    def test_download_redirect_strips_authorization_and_rejects_other_origins(self):
        request = urllib.request.Request('https://api.github.com' + API_PREFIX + '/releases/assets/1',
                                         headers={'Authorization': 'Bearer synthetic-test-value'})
        redirected = SafeRedirect().redirect_request(
            request, None, 302, 'redirect', {},
            'https://release-assets.githubusercontent.com/synthetic/file?signature=test')
        self.assertIsNone(redirected.get_header('Authorization'))
        with self.assertRaisesRegex(PublishError, 'origin'):
            SafeRedirect().redirect_request(request, None, 302, 'redirect', {}, 'https://example.com/file')

    def test_api_rejects_another_repository_before_network(self):
        api = GitHubAPI('synthetic-test-value')
        with self.assertRaisesRegex(PublishError, 'API target'):
            api._request('GET', 'https://api.github.com/repos/other/target/releases')


if __name__ == '__main__':
    unittest.main()
