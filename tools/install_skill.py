"""Install a verified Skill into an explicitly selected local discovery directory."""
from __future__ import annotations

import argparse
import ctypes
import errno
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

if __name__ == '__main__':
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.verify_release_bundle import verify_directory

NAME = 'ranzevor-standards'


def _plain(path: Path) -> None:
    info = path.lstat()
    if (stat.S_ISLNK(info.st_mode) or
            getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        raise ValueError('installation path contains a link or reparse point: ' + str(path))


def _directory(scope: Path, relative: Path, *, create: bool = False) -> Path:
    relative = Path(relative)
    if relative.is_absolute() or relative.drive or '..' in relative.parts:
        raise ValueError('installation directory must be relative to the selected scope')
    current = scope
    _plain(current)
    for part in relative.parts:
        current = current / part
        if not os.path.lexists(current):
            if not create:
                continue
            try:
                current.mkdir()
            except FileExistsError:
                pass
        if os.path.lexists(current):
            _plain(current)
            if not current.is_dir():
                raise ValueError('installation parent is not a directory: ' + str(current))
        if not current.resolve().is_relative_to(scope):
            raise ValueError('installation directory leaves the selected scope')
    return current


def _publish(source: Path, target: Path) -> None:
    """Move the complete directory without replacing even an empty competing target."""
    if os.name == 'nt':
        os.rename(source, target)
        return
    if sys.platform != 'linux':
        raise OSError(errno.ENOTSUP, 'atomic no-replace directory installation is unavailable')
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, 'renameat2', None)
    if rename is None:
        raise OSError(errno.ENOTSUP, 'atomic no-replace directory installation is unavailable')
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    at_fdcwd, rename_noreplace = -100, 1
    if rename(at_fdcwd, os.fsencode(source), at_fdcwd, os.fsencode(target), rename_noreplace) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))


def install(source: Path, scope_root: Path, skills_dir: Path,
            staging_parent: Path = Path('.')) -> dict:
    """Use a staging parent outside the host's discovery roots, within the same scope."""
    source = Path(source)
    _plain(source)
    for entry in source.rglob('*'):
        _plain(entry)
    original = verify_directory(source)
    if original['kind'] != 'agent-skill':
        raise ValueError('installation requires the complete Agent Skill bundle')
    scope = Path(scope_root).resolve(strict=True)
    if not scope.is_dir():
        raise ValueError('selected scope is not a directory')
    skills = _directory(scope, skills_dir)
    staging = _directory(scope, staging_parent)
    if staging.is_relative_to(skills):
        raise ValueError('staging must be outside the Skill discovery directory')
    target = skills / NAME
    actual_source = source.resolve(strict=True)
    if staging.is_relative_to(actual_source) or target.is_relative_to(actual_source):
        raise ValueError('installation and staging must not be inside the source Skill')
    if os.path.lexists(target):
        raise FileExistsError('a Skill already exists at ' + str(target))
    _directory(scope, skills_dir, create=True)
    _directory(scope, staging_parent, create=True)
    with tempfile.TemporaryDirectory(prefix='.standards-install-', dir=staging) as temporary:
        staged = Path(temporary) / NAME
        # Preserve redirected entries rather than following them; verification rejects them.
        shutil.copytree(source, staged, symlinks=True)
        for entry in staged.rglob('*'):
            _plain(entry)
        if verify_directory(staged) != original:
            raise ValueError('the Skill changed while being copied')
        _directory(scope, staging_parent)
        _directory(scope, skills_dir)
        _publish(staged, target)
    return {'version': original['version'], 'path': str(target)}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if callable(getattr(stream, 'reconfigure', None)):
            stream.reconfigure(encoding='utf-8', newline='\n')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--scope-root', type=Path, required=True)
    parser.add_argument('--skills-dir', type=Path, required=True,
                        help='Actual host discovery directory, relative to the selected scope')
    parser.add_argument('--staging-parent', type=Path, default=Path('.'),
                        help='Relative directory outside all actual host discovery roots, on the same volume')
    args = parser.parse_args(argv)
    try:
        result = install(args.source, args.scope_root, args.skills_dir, args.staging_parent)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('installation failed: ' + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
