"""Install a verified Skill into an explicitly selected local discovery directory."""
from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
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


class _WindowsAPI:
    def __init__(self):
        self.dll = ctypes.WinDLL('kernel32', use_last_error=True)
        self.open = self.dll.CreateFileW
        self.open.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                              ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        self.open.restype = ctypes.c_void_p
        self.close = self.dll.CloseHandle
        self.close.argtypes = [ctypes.c_void_p]
        self.close.restype = ctypes.c_int
        self.info = self.dll.GetFileInformationByHandleEx
        self.info.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        self.info.restype = ctypes.c_int
        self.rename = self.dll.SetFileInformationByHandle
        self.rename.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
        self.rename.restype = ctypes.c_int

    def directory(self, path: Path, *, movable: bool = False) -> int:
        # No delete sharing pins ancestors against rename/removal until CloseHandle.
        access = 0x80 | (0x10000 if movable else 0)  # READ_ATTRIBUTES, DELETE
        share = 3 | (4 if movable else 0)  # READ | WRITE, optionally DELETE
        handle = self.open(str(path), access, share, None, 3, 0x02200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            info = (ctypes.c_uint32 * 2)()  # FILE_ATTRIBUTE_TAG_INFO
            if not self.info(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            if info[0] & 0x400 or not info[0] & 0x10:
                raise ValueError('installation parent is not a plain directory: ' + str(path))
            return handle
        except BaseException:
            self.close(handle)
            raise

    def move(self, source: Path, target: Path, parent: int) -> None:
        class RenameInfo(ctypes.Structure):
            _fields_ = [('flags', ctypes.c_uint32), ('root', ctypes.c_void_p),
                        ('length', ctypes.c_uint32), ('name', ctypes.c_wchar * (len(target.name) + 1))]
        info = RenameInfo(0, parent, len(target.name.encode('utf-16-le')), target.name)
        handle = self.directory(source, movable=True)
        try:
            # FileRenameInfo resolves the leaf name against the pinned destination handle.
            if not self.rename(handle, 3, ctypes.byref(info), ctypes.sizeof(info)):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.close(handle)


class _PinnedParent:
    def __init__(self, path: Path, handle: int, links, windows=None):
        self.path, self.handle, self.links, self.windows = path, handle, links, windows

    def check(self) -> None:
        if self.windows is not None:
            # All ancestors are open without delete sharing; their names cannot be replaced.
            return
        for parent, name, child in self.links:
            observed = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if not os.path.samestat(observed, os.fstat(child)):
                raise ValueError('installation parent was replaced: ' + str(self.path))


@contextmanager
def _pin_parent(path: Path):
    """Open each component without following links, and retain it through publication."""
    with ExitStack() as stack:
        current = Path(path.anchor)
        if os.name == 'nt':
            api = _WindowsAPI()
            handle = api.directory(current)
            stack.callback(api.close, handle)
            for part in path.parts[1:]:
                current /= part
                handle = api.directory(current)
                stack.callback(api.close, handle)
            yield _PinnedParent(path, handle, (), api)
        elif sys.platform == 'linux':
            flags = os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            handle = os.open(current, flags)
            stack.callback(os.close, handle)
            links = []
            for part in path.parts[1:]:
                child = os.open(part, flags, dir_fd=handle)
                stack.callback(os.close, child)
                links.append((handle, part, child))
                handle = child
            yield _PinnedParent(path, handle, links)
        else:
            raise OSError(errno.ENOTSUP, 'handle-bound directory installation is unavailable')


def _publish(source: Path, target: Path, *, source_parent: _PinnedParent,
             target_parent: _PinnedParent) -> None:
    """Move between pinned parents, without replacing even an empty competing target."""
    source_parent.check()
    target_parent.check()
    if target_parent.windows is not None:
        target_parent.windows.move(source, target, target_parent.handle)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, 'renameat2', None)
    if rename is None:
        raise OSError(errno.ENOTSUP, 'atomic no-replace directory installation is unavailable')
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    original = os.stat(source.name, dir_fd=source_parent.handle, follow_symlinks=False)
    if rename(source_parent.handle, os.fsencode(source.name), target_parent.handle,
              os.fsencode(target.name), 1) != 0:  # RENAME_NOREPLACE
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))
    try:
        source_parent.check()
        target_parent.check()
    except (OSError, ValueError):
        # Use the same handles to recover our directory; never follow the replacement path.
        moved = os.stat(target.name, dir_fd=target_parent.handle, follow_symlinks=False)
        if not os.path.samestat(original, moved):
            raise ValueError('installed directory changed during publication')
        if rename(target_parent.handle, os.fsencode(target.name), source_parent.handle,
                  os.fsencode(source.name), 1) != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), str(source))
        raise


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
        with _pin_parent(staged.parent) as source_parent, _pin_parent(target.parent) as target_parent:
            _publish(staged, target, source_parent=source_parent, target_parent=target_parent)
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
