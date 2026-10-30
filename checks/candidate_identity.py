"""Capture a Git candidate tree or verify an existing release input identity."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


class CandidateIdentityError(ValueError):
    pass


def _git(root: Path, environment: dict, *arguments: str, data=None, allowed=(0,)):
    command = ['git', '-C', str(root), '-c', 'core.fsmonitor=false',
               '-c', 'core.untrackedCache=false', '-c', 'core.splitIndex=false', *arguments]
    try:
        result = subprocess.run(command, input=data, env=environment, capture_output=True,
                                timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CandidateIdentityError('Git candidate identity could not be read: ' + str(error)) from error
    if result.returncode not in allowed:
        detail = result.stderr.decode('utf-8', 'replace').strip()
        raise CandidateIdentityError('Git candidate identity failed: ' + detail)
    return result


def _head(root: Path, environment: dict):
    result = _git(root, environment, 'rev-parse', '--verify', '--quiet', 'HEAD^{commit}',
                  allowed=(0, 1))
    if result.returncode == 0:
        return result.stdout.decode('ascii').strip()
    branch = _git(root, environment, 'symbolic-ref', '--quiet', 'HEAD').stdout.decode().strip()
    missing = _git(root, environment, 'show-ref', '--verify', '--quiet', branch, allowed=(0, 1))
    if missing.returncode != 1:
        raise CandidateIdentityError('HEAD does not identify a commit or an unborn branch')
    return None


def _git_identity(root: Path):
    environment = dict(os.environ)
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE',
                 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_PREFIX'):
        environment.pop(name, None)
    environment.update(GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0',
                       GIT_NO_REPLACE_OBJECTS='1')
    actual_root = _git(root, environment, 'rev-parse', '--show-toplevel').stdout
    if Path(os.fsdecode(actual_root.rstrip(b'\n'))).resolve() != root:
        raise CandidateIdentityError('source root is not the Git repository root')
    object_format = _git(root, environment, 'rev-parse', '--show-object-format').stdout.decode().strip()
    if object_format not in ('sha1', 'sha256'):
        raise CandidateIdentityError('unsupported Git object format')
    base_commit = _head(root, environment)
    index = Path(os.fsdecode(_git(root, environment, 'rev-parse', '--path-format=absolute',
                                  '--git-path', 'index').stdout.rstrip(b'\n')))
    objects = os.fsdecode(_git(root, environment, 'rev-parse', '--path-format=absolute',
                               '--git-path', 'objects').stdout.rstrip(b'\n'))
    index_bytes = index.read_bytes() if index.is_file() else None
    with tempfile.TemporaryDirectory(prefix='standards-candidate-') as temporary:
        scratch = Path(temporary)
        temporary_index = scratch / 'index'
        temporary_objects = scratch / 'objects'
        temporary_objects.mkdir()
        isolated = dict(environment, GIT_INDEX_FILE=str(temporary_index),
                        GIT_OBJECT_DIRECTORY=str(temporary_objects),
                        GIT_ALTERNATE_OBJECT_DIRECTORIES=json.dumps(objects, ensure_ascii=False))
        # Preserve the current tracked set, including staged additions/removals.
        # Renormalization refreshes file content independently of cached stat data.
        if index_bytes is not None:
            temporary_index.write_bytes(index_bytes)
        else:
            _git(root, isolated, 'read-tree', '--empty')
        _git(root, isolated, '-c', 'core.sparseCheckout=false', 'add', '-A', '--', '.')
        _git(root, isolated, '-c', 'core.sparseCheckout=false', 'add', '--renormalize', '-A', '--', '.')
        tree = _git(root, isolated, 'write-tree').stdout.decode('ascii').strip()
    if _head(root, environment) != base_commit:
        raise CandidateIdentityError('Git HEAD changed while capturing the candidate')
    length = 40 if object_format == 'sha1' else 64
    if re.fullmatch('[0-9a-f]{' + str(length) + '}', tree) is None:
        raise CandidateIdentityError('Git returned an invalid candidate tree')
    return {'kind': 'git', 'object_format': object_format,
            'base_commit': base_commit, 'tree': tree}


def capture_source_identity(source_root: Path):
    """Bind current source, including uncommitted Git edits, without a file manifest."""
    root = Path(source_root).resolve()
    if not root.is_dir():
        raise CandidateIdentityError('source root is not a directory')
    if os.path.lexists(root / '.git'):
        return _git_identity(root)
    from tools.verify_release_bundle import MANIFEST, verify_directory
    if (root.parent / MANIFEST).exists():
        verified = verify_directory(root.parent)
        expected = 'source' if verified['kind'] == 'source' else 'references'
        if root.name != expected:
            raise CandidateIdentityError('source root does not match the verified bundle kind')
        return {'kind': 'release-bundle', 'bundle_kind': verified['kind'],
                'version': verified['version'],
                'source_tree_sha256': verified['source_tree_sha256'],
                'manifest_sha256': verified['manifest_sha256']}
    return _git_identity(root)


def verify_source_unchanged(source_root: Path, before: dict):
    after = capture_source_identity(source_root)
    if after != before:
        raise CandidateIdentityError('tested source changed during execution')
    return after
