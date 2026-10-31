"""Publish an exact, locally verified Standards release; never replace published bytes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_release_bundle import clean_git_identity, read_source
from tools.verify_release_artifacts import asset_names, local_assets
from tools.verify_release_bundle import (
    MAX_BYTES, canonical, parse_json, validate_project_release, validate_release_config,
)

REPOSITORY = 'ranzevor/Standards'
API_PREFIX = '/repos/' + REPOSITORY
API_VERSION = '2026-03-10'
TAGGER_NAME = 'Standards Release Automation'
TAGGER_EMAIL = 'standards-release@automation.invalid'
TAG_READBACK_DELAYS = (0, 1, 2, 4)

class PublishError(ValueError):
    pass


class APIError(PublishError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def require(condition, message):
    if not condition:
        raise PublishError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    """Keep the token on GitHub's API; signed download URLs do not need it."""
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        target = urllib.parse.urlsplit(new_url)
        require(target.scheme == 'https' and target.hostname in {
            'api.github.com', 'release-assets.githubusercontent.com',
            'objects.githubusercontent.com', 'github.com',
        }, 'unexpected download redirect origin')
        redirected = super().redirect_request(
            request, file_pointer, code, message, headers, new_url)
        if redirected is not None and target.hostname != urllib.parse.urlsplit(request.full_url).hostname:
            redirected.remove_header('Authorization')
        return redirected


class GitHubAPI:
    def __init__(self, token):
        require(isinstance(token, str) and bool(token), 'GitHub token is required')
        self.token = token
        self.opener = urllib.request.build_opener(SafeRedirect())

    def _request(self, method, url, data=None, content_type=None, binary=False, missing=False):
        parsed = urllib.parse.urlsplit(url)
        require(parsed.scheme == 'https' and parsed.hostname in {'api.github.com', 'uploads.github.com'}
                and parsed.path.startswith(API_PREFIX + '/'), 'unexpected GitHub API target')
        headers = {
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/octet-stream' if binary else 'application/vnd.github+json',
            'X-GitHub-Api-Version': API_VERSION,
            'User-Agent': 'Standards-release',
        }
        if content_type:
            headers['Content-Type'] = content_type
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=60) as response:
                raw = response.read(MAX_BYTES + 1)
                require(len(raw) <= MAX_BYTES, 'GitHub response exceeds the byte limit')
                if binary:
                    return raw
                return parse_json(raw) if raw else None
        except urllib.error.HTTPError as error:
            if missing and error.code == 404:
                return None
            raise APIError(error.code, f'GitHub API {error.code}: {method} {parsed.path}') from None
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise APIError(None, f'GitHub API outcome unknown: {method} {parsed.path}') from error

    def request(self, method, suffix, payload=None, missing=False):
        require(suffix.startswith('/') and not suffix.startswith('//'), 'invalid API suffix')
        return self._request(method, 'https://api.github.com' + API_PREFIX + suffix,
                             canonical(payload) if payload is not None else None,
                             'application/json' if payload is not None else None,
                             missing=missing)

    def upload(self, release, name, raw):
        base = release['upload_url'].split('{', 1)[0]
        require(base == f'https://uploads.github.com{API_PREFIX}/releases/{release["id"]}/assets',
                'unexpected release upload URL')
        kind = 'application/zip' if name.endswith('.zip') else (
            'application/json' if name.endswith('.json') else 'text/plain; charset=utf-8')
        return self._request('POST', base + '?' + urllib.parse.urlencode({'name': name}),
                             raw, kind)

    def download(self, asset):
        require(type(asset.get('id')) is int and asset['id'] > 0, 'invalid asset ID')
        return self._request('GET', f'https://api.github.com{API_PREFIX}/releases/assets/{asset["id"]}',
                             binary=True)


def collection(api, suffix):
    rows = []
    for page in range(1, 101):
        batch = api.request('GET', suffix + f'?per_page=100&page={page}')
        require(type(batch) is list, 'invalid paginated GitHub collection')
        rows.extend(batch)
        if len(batch) < 100:
            return rows
    raise PublishError('GitHub collection exceeded the pagination limit')


def find_release(api, tag):
    matches = [r for r in collection(api, '/releases') if r.get('tag_name') == tag]
    require(len(matches) <= 1, 'multiple releases have the same tag')
    return matches[0] if matches else None


def peel_tag(api, target):
    for _ in range(8):
        require(re.fullmatch('[0-9a-f]{40}', target.get('sha', '')) is not None, 'invalid tag target')
        if target.get('type') == 'commit':
            return target['sha']
        require(target.get('type') == 'tag', 'tag does not resolve to a commit')
        record = api.request('GET', '/git/tags/' + target['sha'])
        require(record.get('sha') == target['sha'], 'tag object readback identity differs')
        target = record.get('object', {})
    raise PublishError('tag indirection limit exceeded')


def tag_commit(api, tag):
    value = api.request('GET', '/git/ref/tags/' + tag, missing=True)
    return None if value is None else peel_tag(api, value.get('object', {}))


def tag_payload(tag, commit, notes, committed_at):
    require(re.fullmatch(r'v0\.1\.(?:0|[1-9][0-9]*)', tag or '') is not None,
            'invalid release tag name')
    require(re.fullmatch('[0-9a-f]{40}', commit or '') is not None, 'invalid tag commit')
    require(type(committed_at) is str and re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})', committed_at),
        'invalid source committer date')
    timestamp = datetime.fromisoformat(committed_at.replace('Z', '+00:00')).astimezone(timezone.utc)
    date = timestamp.isoformat(timespec='seconds').replace('+00:00', 'Z')
    message = (f'Standards {tag}\n\nSource commit: {commit}\n'
               f'Release notes SHA-256: {sha256(notes.encode("utf-8"))}\n'
               'Signature policy: unsigned\n'
               'Tagger date policy: source commit committer date, not publication time\n')
    return {'tag': tag, 'object': commit, 'type': 'commit', 'message': message,
            'tagger': {'name': TAGGER_NAME, 'email': TAGGER_EMAIL, 'date': date}}


def tag_object_bytes(payload):
    tagger = payload['tagger']
    timestamp = int(datetime.fromisoformat(tagger['date'].replace('Z', '+00:00')).timestamp())
    return (f'object {payload["object"]}\ntype commit\ntag {payload["tag"]}\n'
            f'tagger {tagger["name"]} <{tagger["email"]}> {timestamp} +0000\n\n'
            + payload['message']).encode('utf-8')


def tag_object_id(payload):
    raw = tag_object_bytes(payload)
    return hashlib.sha1(b'tag ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def check_tag_object(record, payload, object_id):
    require(type(record) is dict and record.get('sha') == object_id and
            all(record.get(key) == payload[key] for key in ('tag', 'message')) and
            record.get('object', {}).get('type') == 'commit' and
            record.get('object', {}).get('sha') == payload['object'] and
            all(record.get('tagger', {}).get(key) == value for key, value in payload['tagger'].items()),
            'annotated tag object differs from the intended immutable identity')
    verification = record.get('verification', {})
    require(verification.get('verified') is False and verification.get('reason') == 'unsigned'
            and verification.get('signature') is None, 'new tag is not the expected unsigned object')


def tag_receipt(api, tag, commit):
    ref = api.request('GET', '/git/ref/tags/' + tag)
    target = ref.get('object', {})
    require(peel_tag(api, target) == commit, 'tag no longer resolves to the intended commit')
    if target.get('type') == 'commit':
        return {'name': tag, 'kind': 'lightweight', 'object_sha': None,
                'peeled_commit': commit, 'signature': 'not-present'}
    require(target.get('type') == 'tag', 'invalid release tag reference')
    record = api.request('GET', '/git/tags/' + target['sha'])
    require(record.get('sha') == target['sha'], 'tag object readback identity differs')
    verification = record.get('verification', {})
    unsigned = (verification.get('verified') is False and verification.get('reason') == 'unsigned'
                and verification.get('signature') is None)
    return {'name': tag, 'kind': 'annotated', 'object_sha': target['sha'],
            'peeled_commit': commit, 'signature': 'unsigned' if unsigned else 'not-verified-by-this-tool'}


def confirm_tag_readback(api, suffix):
    """Confirm one created object using bounded reads, without repeating a write."""
    last_failure = 'object not visible'
    for delay in TAG_READBACK_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            record = api.request('GET', suffix, missing=True)
        except APIError as error:
            if error.status not in {None, 404, 408, 429, 500, 502, 503, 504}:
                raise
            last_failure = 'transport failure' if error.status is None else f'HTTP {error.status}'
        else:
            if record is not None:
                return record
            last_failure = 'HTTP 404'
    raise APIError(None, f'tag confirmation incomplete: GET {suffix}; last read: {last_failure}; '
                   'publication stopped; reconcile the same release identity before resuming')


def ensure_tag(api, tag, commit, notes):
    ref = api.request('GET', '/git/ref/tags/' + tag, missing=True)
    require(ref is None or ref.get('object', {}).get('type') == 'tag',
            'unpublished release has a lightweight tag; it will not be replaced')
    source = api.request('GET', '/git/commits/' + commit)
    require(source.get('sha') == commit, 'tag source commit identity differs')
    payload = tag_payload(tag, commit, notes, source.get('committer', {}).get('date'))
    object_id = tag_object_id(payload)
    require(ref is None or ref.get('object', {}).get('sha') == object_id,
            'existing annotated tag differs; it will not be moved')
    record = api.request('GET', '/git/tags/' + object_id, missing=True)
    if record is None:
        try:
            created = api.request('POST', '/git/tags', payload)
        except APIError as error:
            if error.status in {401, 403}:
                raise
            # Reconcile only this content-addressed object; never invent another tag identity.
            record = confirm_tag_readback(api, '/git/tags/' + object_id)
        else:
            check_tag_object(created, payload, object_id)
            record = confirm_tag_readback(api, '/git/tags/' + object_id)
    check_tag_object(record, payload, object_id)
    ref = api.request('GET', '/git/ref/tags/' + tag, missing=True)
    if ref is None:
        try:
            api.request('POST', '/git/refs', {'ref': 'refs/tags/' + tag, 'sha': object_id})
        except APIError as error:
            if error.status in {401, 403}:
                raise
            ref = confirm_tag_readback(api, '/git/ref/tags/' + tag)
        else:
            ref = confirm_tag_readback(api, '/git/ref/tags/' + tag)
    require(ref.get('object', {}).get('type') == 'tag' and
            ref.get('object', {}).get('sha') == object_id,
            'release tag ref differs; it will not be moved')
    check_tag_object(api.request('GET', '/git/tags/' + object_id), payload, object_id)
    intended = {'name': tag, 'kind': 'annotated', 'object_sha': object_id,
                'peeled_commit': commit, 'signature': 'unsigned'}
    require(tag_receipt(api, tag, commit) == intended,
            'tag changed before its intended identity was confirmed')
    return intended


def verify_published_tag(api, tag, commit, notes):
    """Read back the complete immutable tag identity without creating objects."""
    source = api.request('GET', '/git/commits/' + commit)
    require(source.get('sha') == commit, 'tag source commit identity differs')
    payload = tag_payload(tag, commit, notes, source.get('committer', {}).get('date'))
    object_id = tag_object_id(payload)
    ref = api.request('GET', '/git/ref/tags/' + tag)
    require(ref.get('object', {}).get('type') == 'tag' and
            ref.get('object', {}).get('sha') == object_id,
            'published annotated tag differs from the intended immutable identity')
    check_tag_object(api.request('GET', '/git/tags/' + object_id), payload, object_id)
    confirmed = api.request('GET', '/git/ref/tags/' + tag)
    require(confirmed.get('object', {}).get('type') == 'tag' and
            confirmed.get('object', {}).get('sha') == object_id,
            'published annotated tag changed during verification')
    return {'name': tag, 'kind': 'annotated', 'object_sha': object_id,
            'peeled_commit': commit, 'signature': 'unsigned'}


def release_assets(api, release_id):
    items = collection(api, f'/releases/{release_id}/assets')
    result = {}
    for item in items:
        require(type(item) is dict and type(item.get('name')) is str, 'invalid remote asset')
        require(item['name'] not in result, 'duplicate remote asset name')
        result[item['name']] = item
    return result


def check_asset(api, asset, expected):
    require(asset.get('state') == 'uploaded' and type(asset.get('size')) is int
            and asset['size'] == len(expected), 'remote asset state or length mismatch')
    expected_digest = 'sha256:' + sha256(expected)
    if asset.get('digest') is not None:
        require(asset['digest'] == expected_digest, 'remote asset digest metadata mismatch')
    raw = api.download(asset)
    require(len(raw) == len(expected) and sha256(raw) == sha256(expected),
            'remote asset downloaded bytes differ')


def verify_remote_assets(api, release, assets):
    remote = release_assets(api, release['id'])
    require(set(remote) == set(assets), 'remote release asset set differs')
    for name, raw in assets.items():
        check_asset(api, remote[name], raw)


def check_release_identity(release, tag, commit, notes):
    require(release.get('tag_name') == tag and release.get('target_commitish') == commit
            and release.get('name') == 'Standards ' + tag and release.get('prerelease') is False
            and release.get('body') == notes, 'release metadata differs from the intended identity')


def check_initial_release_order(api, tag):
    require(all(item.get('tag_name') == tag or item.get('draft') is True
                for item in collection(api, '/releases')),
            'initial release repository already contains another published release')


def publish(api, config, assets, commit, notes, verify_only=False):
    validate_release_config(config)
    require(re.fullmatch('[0-9a-f]{40}', commit or '') is not None, 'invalid source commit')
    require(set(assets) == set(asset_names(config['version']))
            and all(type(raw) is bytes for raw in assets.values()), 'invalid local asset set')
    tag = 'v' + config['version']
    release = find_release(api, tag)
    current_tag = tag_commit(api, tag)
    require(current_tag is None or current_tag == commit, 'tag identity conflict')
    if release is not None:
        check_release_identity(release, tag, commit, notes)
        if release.get('draft') is False:
            require(bool(release.get('published_at')), 'release publication time is missing')
            require(current_tag == commit, 'published release tag is missing')
            intended_tag = verify_published_tag(api, tag, commit, notes)
            verify_remote_assets(api, release, assets)
            require(verify_published_tag(api, tag, commit, notes) == intended_tag,
                    'published tag changed during asset verification')
            return {'status': 'published-and-verified', 'reused': True,
                    'version': config['version'], 'source_commit': commit, 'url': release['html_url'],
                    'tag': intended_tag}
    require(not verify_only, 'release is not published')
    main = api.request('GET', '/git/ref/heads/main')
    require(main.get('object', {}).get('sha') == commit, 'main changed; revalidate the release target')
    if config['previous_version'] is None:
        check_initial_release_order(api, tag)
    else:
        previous_tag = 'v' + config['previous_version']
        previous = find_release(api, previous_tag)
        require(previous is not None and previous.get('draft') is False and
                previous.get('prerelease') is False, 'previous patch release is not published')
        require(tag_commit(api, previous_tag) is not None, 'previous release tag is missing')
        comparison = api.request('GET', f'/compare/{previous_tag}...{commit}')
        require(comparison.get('status') == 'ahead', 'release commit is not ahead of the previous tag')
    intended_tag = ensure_tag(api, tag, commit, notes)
    if release is None:
        payload = {'tag_name': tag, 'target_commitish': commit, 'name': 'Standards ' + tag,
                   'body': notes, 'draft': True, 'prerelease': False,
                   'generate_release_notes': False}
        try:
            release = api.request('POST', '/releases', payload)
        except APIError:
            release = find_release(api, tag)
            if release is None:
                raise
        check_release_identity(release, tag, commit, notes)
    require(release.get('draft') is True, 'release changed while preparing publication')
    remote = release_assets(api, release['id'])
    require(set(remote) <= set(assets), 'draft contains unexpected assets')
    for name, raw in assets.items():
        existing = remote.get(name)
        if existing is not None and existing.get('state') == 'starter' and existing.get('size') == 0:
            # Delete only a failed empty upload on this still-unpublished release.
            latest = api.request('GET', f'/releases/{release["id"]}')
            require(latest.get('draft') is True, 'release was published during upload recovery')
            api.request('DELETE', '/releases/assets/' + str(existing['id']))
            existing = None
        if existing is None:
            try:
                api.upload(release, name, raw)
            except APIError:
                # Re-read before a retry; never blindly repeat an upload.
                existing = release_assets(api, release['id']).get(name)
                if existing is None:
                    raise
            else:
                existing = release_assets(api, release['id']).get(name)
            require(existing is not None, 'uploaded asset has not become visible')
        check_asset(api, existing, raw)
    verify_remote_assets(api, release, assets)
    require(tag_receipt(api, tag, commit) == intended_tag, 'tag changed before publication')
    main = api.request('GET', '/git/ref/heads/main')
    require(main.get('object', {}).get('sha') == commit, 'main changed before publication')
    latest = api.request('GET', f'/releases/{release["id"]}')
    check_release_identity(latest, tag, commit, notes)
    if latest.get('draft') is True:
        if config['previous_version'] is None:
            check_initial_release_order(api, tag)
        try:
            api.request('PATCH', f'/releases/{release["id"]}', {'draft': False, 'make_latest': 'true'})
        except APIError:
            latest = api.request('GET', f'/releases/{release["id"]}')
            if latest.get('draft') is not False:
                raise
    final = api.request('GET', f'/releases/{release["id"]}')
    check_release_identity(final, tag, commit, notes)
    require(final.get('draft') is False and bool(final.get('published_at')), 'release was not published')
    require(verify_published_tag(api, tag, commit, notes) == intended_tag,
            'published tag identity differs')
    verify_remote_assets(api, final, assets)
    require(verify_published_tag(api, tag, commit, notes) == intended_tag,
            'published tag changed during asset verification')
    return {'status': 'published-and-verified', 'reused': False,
            'version': config['version'], 'source_commit': commit, 'url': final['html_url'],
            'tag': intended_tag}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--source-commit', required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--publish', action='store_true')
    mode.add_argument('--verify-published', action='store_true')
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        source = read_source(root)
        identity = clean_git_identity(root, args.source_commit, source)
        config = validate_release_config(parse_json(source['releases/current.json']))
        validate_project_release(parse_json(source['project.json']), config['version'])
        digest = sha256(canonical(sorted((key, len(raw), sha256(raw)) for key, raw in source.items())))
        assets = local_assets(args.artifacts, config['version'], identity, digest)
        notes = source[config['notes_path']].decode('utf-8')
        if args.publish or args.verify_published:
            require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY, 'unexpected publishing repository')
            result = publish(GitHubAPI(os.environ.get('GH_TOKEN')), config, assets,
                             args.source_commit, notes, args.verify_published)
        else:
            result = {'status': 'local-artifacts-verified', 'version': config['version'],
                      **identity, 'assets': {name: sha256(raw) for name, raw in assets.items()}}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        print('release publication failed: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
