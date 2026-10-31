"""Finite examples of independent package expectations and version-neutral recovery."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from tools.verify_release_bundle import checked_path, check_path_set, parse_json


class ContractError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def inventory(files):
    """Describe a finite map of regular files; directory entries are out of scope."""
    require(type(files) is dict, 'file map required')
    require(all(type(name) is str and type(raw) is bytes for name, raw in files.items()),
            'path and byte content required')
    try:
        check_path_set(files)
    except ValueError as error:
        raise ContractError(str(error)) from error
    result = {name: {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
              for name, raw in files.items()}
    return result


def file_identity(files):
    raw = json.dumps(inventory(files), ensure_ascii=False, sort_keys=True,
                     separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def expected_package(source, version):
    """The example's packaging contract, supplied independently of the built artifact."""
    require(type(version) is str and re.fullmatch(r'0\.1\.(?:0|[1-9][0-9]*)', version),
            'example patch version required')
    return {
        'demo_reader/__init__.py': source['src/demo_reader/__init__.py'],
        'demo_reader/py.typed': source['src/demo_reader/py.typed'],
        'LICENSE': source['LICENSE'],
        'metadata.json': json.dumps({'name': 'demo-reader', 'version': version},
                                    sort_keys=True).encode('utf-8'),
    }


def verify_package(files, declared_inventory, expected, source_files, source_manifest_sha256):
    require(inventory(files) == declared_inventory, 'artifact inventory differs')
    require(files == expected, 'package contract differs')
    require(file_identity(source_files) == source_manifest_sha256,
            'source manifest identity differs')
    return file_identity(files)


def include_targets(text, required):
    """Only independent '-r relative-file' entries and comments belong to this grammar."""
    targets = []
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r'-r\s+([^\s]+)', line)
        require(match is not None, 'unsupported include syntax')
        targets.append(match[1])
    require(len(targets) == len(set(targets)) and set(targets) == set(required),
            'include targets differ')
    return frozenset(targets)


def read_config(path):
    raw = Path(path).read_bytes()
    try:
        value = parse_json(raw)
    except ValueError as error:
        raise ContractError(str(error)) from error
    require(type(value) is dict and set(value) == {'workers'}
            and type(value['workers']) is int and 1 <= value['workers'] <= 16,
            'workers must be an integer from 1 to 16')
    return value, hashlib.sha256(raw).hexdigest()


def resolve_member(root, relative):
    """Resolve a member in a controlled tree; this does not lock paths against writers."""
    try:
        checked_path(relative)
        physical_root = Path(root).resolve(strict=True)
        member = physical_root.joinpath(*relative.split('/')).resolve(strict=True)
        require(member.is_relative_to(physical_root) and member.is_file(),
                'member is outside the physical root or is not a file')
        return member
    except (ValueError, OSError) as error:
        raise ContractError(str(error)) from error


def switch_owned_files(current, expected_current_identity, incoming, trusted_incoming_identity):
    """Model an owned-file transition; filesystem transactions and user data are separate."""
    require(file_identity(current) == expected_current_identity, 'current installation differs')
    require(file_identity(incoming) == trusted_incoming_identity, 'incoming release differs')
    return dict(incoming)
