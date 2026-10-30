"""Verify four local release artifacts against an exact source commit for manual handoff."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_release_bundle import (
    archive_names, clean_git_identity, read_source, sha256, verify_normative,
)
from tools.verify_release_bundle import MAX_BYTES, canonical, parse_json, verify_zip

REPORT_FIELDS = {
    'status', 'version', 'documents', 'adopted_documents', 'current_snapshot_sha256',
    'source_tree_sha256', 'archives', 'public_distribution_authorized', 'license_grant',
    'source_commit', 'source_git_tree',
}

class ArtifactError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ArtifactError(message)


def asset_names(version):
    return (*archive_names(version), 'SHA256SUMS.txt', 'BUILD-REPORT.json')


def local_assets(directory, version, identity, source_digest):
    """Verify the transfer artifact against the independently checked-out source."""
    directory = Path(directory)
    require(directory.is_dir() and not directory.is_symlink(), 'invalid artifact directory')
    expected = asset_names(version)
    require({p.name for p in directory.iterdir()} == set(expected), 'local asset set differs')
    assets = {}
    for name in expected:
        path = directory / name
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_BYTES,
                'invalid local asset file')
        assets[name] = path.read_bytes()
    report = parse_json(assets['BUILD-REPORT.json'])
    require(type(report) is dict and set(report) == REPORT_FIELDS, 'invalid build report fields')
    require(report['status'] == 'built-and-file-verified' and
            report['version'] == version and report['public_distribution_authorized'] is True and
            report['license_grant'] == 'multi-license: CC-BY-4.0 and Apache-2.0',
            'build report identity differs')
    require(all(report[key] == value for key, value in identity.items()), 'build source commit/tree differs')
    require(report['source_tree_sha256'] == source_digest, 'built bytes differ from checked-out source')
    names = archive_names(version)
    require(type(report['archives']) is dict and set(report['archives']) == set(names),
            'build report archive set differs')
    for name in names:
        actual = verify_zip(directory / name)
        require(actual == report['archives'][name], 'archive and build report differ')
        require(actual['sha256'] == sha256(assets[name]), 'archive changed during verification')
        require(actual['version'] == version and
                actual['source_tree_sha256'] == source_digest and
                actual['current_snapshot_sha256'] == report['current_snapshot_sha256'] and
                actual['documents'] == report['documents'] and
                actual['adopted'] == report['adopted_documents'], 'archive source identity differs')
    summed = (*names, 'BUILD-REPORT.json')
    sums = ''.join(sha256(assets[name]) + '  ' + name + '\n'
                   for name in summed).encode('utf-8')
    require(assets['SHA256SUMS.txt'] == sums, 'SHA256SUMS differs from actual archives/report')
    return assets


def verify_artifacts(root, directory, commit):
    root = Path(root).resolve()
    source = read_source(root)
    identity = clean_git_identity(root, commit, source)
    version = verify_normative(source)['version']
    digest = sha256(canonical(sorted((key, len(raw), sha256(raw)) for key, raw in source.items())))
    assets = local_assets(directory, version, identity, digest)
    return {'status': 'local-artifacts-verified', 'version': version,
            **identity, 'assets': {name: sha256(raw) for name, raw in assets.items()}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--source-commit', required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_artifacts(args.root, args.artifacts, args.source_commit)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        print('release artifact verification failed: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
