"""Executable Git state-transition examples with semantic assertions and JSON evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import traceback


class ScenarioFailure(AssertionError):
    """A state or command differed from the explicitly recorded expectation."""


class Sandbox:
    def __init__(self, root: Path, mutation: str | None = None):
        self.root = root.resolve()
        self.mutation = mutation
        self.commands = []
        self.checks = []
        self.snapshots = []
        self.repos = []
        for name in ('home', 'xdg', 'empty-template'):
            (self.root / name).mkdir()
        self.env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'HOME': str(self.root / 'home'),
            'XDG_CONFIG_HOME': str(self.root / 'xdg'),
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_SYSTEM': os.devnull,
            'GIT_CONFIG_GLOBAL': os.devnull,
            'GIT_ALLOW_PROTOCOL': 'file',
            'GIT_TERMINAL_PROMPT': '0',
            'GIT_EDITOR': 'true',
            'GIT_SEQUENCE_EDITOR': 'true',
            'GIT_MERGE_AUTOEDIT': 'no',
            'GIT_AUTHOR_DATE': '2026-01-01T00:00:00+00:00',
            'GIT_COMMITTER_DATE': '2026-01-01T00:00:00+00:00',
            'LC_ALL': 'C',
        }
        self.prefix = [
            'git', '-c', 'core.hooksPath=' + os.devnull,
            '-c', 'credential.helper=', '-c', 'protocol.allow=never',
            '-c', 'protocol.file.allow=always', '-c', 'commit.gpgsign=false',
            '-c', 'tag.gpgsign=false', '-c', 'core.autocrlf=false',
            '-c', 'init.templateDir=' + str(self.root / 'empty-template'),
            '-c', 'user.name=Example Author', '-c', 'user.email=example@example.invalid',
        ]

    def git(self, repo: Path, *args: str, expected=0):
        cwd = repo.resolve()
        if not cwd.is_relative_to(self.root):
            raise ValueError('Git working directory must be inside its new sandbox')
        command = self.prefix + list(args)
        try:
            p = subprocess.run(command, cwd=cwd, env=self.env, capture_output=True,
                               text=True, encoding='utf-8', errors='replace', timeout=30)
        except (subprocess.TimeoutExpired, OSError) as exc:
            def text_value(value):
                return value.decode('utf-8', 'replace') if isinstance(value, bytes) else (value or '')
            self.commands.append({'cwd': str(cwd.relative_to(self.root)), 'argv': command,
                                  'expected_exit': expected, 'actual_exit': None,
                                  'outcome': 'timeout' if isinstance(exc, subprocess.TimeoutExpired) else 'not-started',
                                  'stdout': text_value(getattr(exc, 'stdout', '')),
                                  'stderr': text_value(getattr(exc, 'stderr', '')),
                                  'error': str(exc), 'matches': False})
            raise
        match = p.returncode != 0 if expected == 'nonzero' else (
            True if expected is None else p.returncode == expected)
        self.commands.append({'cwd': str(cwd.relative_to(self.root)),
                              'argv': command, 'expected_exit': expected,
                              'actual_exit': p.returncode, 'stdout': p.stdout,
                              'stderr': p.stderr, 'matches': match})
        if not match:
            raise ScenarioFailure(f'command exit: {args}: {p.returncode} != {expected}')
        return p.stdout

    def eq(self, ident, actual, expected):
        ok = actual == expected
        self.checks.append({'id': ident, 'expected': expected, 'actual': actual, 'matches': ok})
        if not ok:
            raise ScenarioFailure(ident)

    def write(self, repo, name, content):
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def init(self, name, bare=False):
        p = self.root / name
        args = ['init', '-b', 'main'] + (['--bare'] if bare else []) + [str(p)]
        self.git(self.root, *args)
        self.repos.append((p, bare))
        return p

    def clone(self, source, name):
        if not source.resolve().is_relative_to(self.root):
            raise ValueError('clone source must be synthetic')
        p = self.root / name
        self.git(self.root, 'clone', '--no-local', '--no-recurse-submodules',
                 source.as_uri(), str(p))
        self.repos.append((p, False))
        return p

    def head(self, repo):
        return self.git(repo, 'rev-parse', 'HEAD').strip()

    def commit(self, repo, message, *paths):
        self.git(repo, 'add', '--', *paths)
        self.git(repo, 'commit', '-m', message)
        return self.head(repo)

    def seeded(self, name='repo'):
        p = self.init(name)
        self.eq('init.unborn-symbolic-head', self.git(p, 'symbolic-ref', 'HEAD').strip(),
                'refs/heads/main')
        self.git(p, 'rev-parse', '--verify', 'HEAD', expected='nonzero')
        self.write(p, 'a.txt', 'base\n')
        self.write(p, 'b.txt', 'base-b\n')
        self.commit(p, 'Base content', 'a.txt', 'b.txt')
        return p

    def snapshot(self, repo, label):
        result = {'label': label, 'repo': str(repo.relative_to(self.root)),
                  'head': self.head(repo),
                  'index': self.git(repo, 'ls-files', '--stage'),
                  'unmerged': self.git(repo, 'ls-files', '-u'),
                  'status': self.git(repo, 'status', '--porcelain=v1', '-uall'),
                  'graph': self.git(repo, 'log', '--all', '--graph', '--format=%H %P %s'),
                  'files': {}}
        for p in sorted(repo.rglob('*')):
            rel = p.relative_to(repo)
            if '.git' in rel.parts or not p.is_file() or p.is_symlink():
                continue
            data = p.read_bytes()
            result['files'][str(rel)] = {'bytes': len(data),
                'sha256': hashlib.sha256(data).hexdigest(),
                'text': data.decode('utf-8', 'replace') if len(data) <= 4096 else None}
        self.snapshots.append(result)
        return result

    def state(self, repo):
        return {'head': self.head(repo), 'index': self.git(repo, 'ls-files', '--stage'),
                'status': self.git(repo, 'status', '--porcelain=v1', '-uall'),
                'a': (repo / 'a.txt').read_text(), 'b': (repo / 'b.txt').read_text()}


def index_snapshot(s):
    p = s.seeded()
    before = s.head(p)
    s.write(p, 'a.txt', 'staged\n')
    s.git(p, 'add', '--', 'a.txt')
    s.write(p, 'a.txt', 'later-worktree\n')
    s.write(p, 'b.txt', 'unrelated\n')
    s.eq('index.staged-copy', s.git(p, 'show', ':a.txt'), 'staged\n')
    s.eq('index.head-unchanged-before-commit', s.head(p), before)
    s.eq('index.double-modified-status', 'MM a.txt' in s.git(p, 'status', '--porcelain=v1'), True)
    s.eq('index.unstaged-diff', '+later-worktree' in s.git(p, 'diff', '--', 'a.txt'), True)
    s.eq('index.staged-diff', '+staged' in s.git(p, 'diff', '--cached', '--', 'a.txt'), True)
    if s.mutation == 'commit-all':
        s.git(p, 'commit', '-am', 'Over-broad staged content')
    else:
        s.git(p, 'commit', '-m', 'Record reviewed index')
    s.eq('index.commit-uses-reviewed-index', s.git(p, 'show', 'HEAD:a.txt'), 'staged\n')
    s.eq('index.unrelated-not-committed', s.git(p, 'show', 'HEAD:b.txt'), 'base-b\n')
    s.eq('index.later-edit-survives', (p / 'a.txt').read_text(), 'later-worktree\n')
    s.eq('index.parent', s.git(p, 'rev-parse', 'HEAD^').strip(), before)
    s.git(p, 'add', '--', 'b.txt')
    s.write(p, 'b.txt', 'later-b-worktree\n')
    s.git(p, 'restore', '--worktree' if s.mutation == 'restore-worktree-instead-of-index' else '--staged', '--', 'b.txt')
    s.eq('restore.unstage-preserves-worktree', (p / 'b.txt').read_text(), 'later-b-worktree\n')
    s.eq('restore.unstage-index', s.git(p, 'show', ':b.txt'), 'base-b\n')
    s.snapshot(p, 'reviewed-index-versus-later-worktree')


def ignore_rules(s):
    p = s.seeded()
    s.write(p, 'tracked.log', 'tracked\n')
    s.commit(p, 'Track a text log', 'tracked.log')
    s.write(p, '.gitignore', '*.log\nbuild/*\n!build/keep.txt\n')
    s.write(p, 'ignored.log', 'generated\n')
    s.write(p, 'build/drop.txt', 'generated\n')
    s.write(p, 'build/keep.txt', 'retained\n')
    s.write(p, 'tracked.log', 'still-tracked\n')
    s.git(p, 'add', '--', 'ignored.log', expected='nonzero')
    s.eq('ignore.source-line', '*.log' in s.git(p, 'check-ignore', '-v', 'ignored.log'), True)
    s.git(p, 'add', '--', '.gitignore', 'tracked.log', 'build/keep.txt')
    names = s.git(p, 'diff', '--cached', '--name-only').splitlines()
    s.eq('ignore.tracked-is-not-excluded', 'tracked.log' in names, True)
    s.eq('ignore.negated-neighbor', 'build/keep.txt' in names, True)
    s.eq('ignore.generated-not-staged', 'build/drop.txt' in s.git(p, 'ls-files').splitlines(), False)
    if s.mutation == 'force-add-ignored':
        s.git(p, 'add', '-f', '--', 'ignored.log')
    s.eq('ignore.excluded-not-staged', 'ignored.log' in s.git(p, 'ls-files').splitlines(), False)
    s.snapshot(p, 'ignore-is-not-removal-or-secret-protection')


def dirty_switch(s):
    p = s.seeded()
    s.git(p, 'switch', '-c', 'feature/change')
    s.write(p, 'a.txt', 'topic\n')
    s.commit(p, 'Change topic', 'a.txt')
    s.git(p, 'switch', 'main')
    s.write(p, 'a.txt', 'valuable-uncommitted\n')
    s.write(p, 'new.txt', 'untracked\n')
    before = s.state(p)
    s.git(p, 'switch', 'feature/change', expected='nonzero')
    s.eq('switch.refusal-preserves-state', s.state(p), before)
    s.git(p, 'stash', 'push', '-u', '-m', 'Before topic switch')
    stash = s.git(p, 'rev-parse', 'refs/stash').strip()
    s.eq('stash.untracked-is-saved', s.git(p, 'show', stash + '^3:new.txt'), 'untracked\n')
    s.git(p, 'switch', 'feature/change')
    s.git(p, 'switch', 'main')
    s.git(p, 'stash', 'apply', '--index', stash)
    s.eq('switch.restored-content', (p / 'a.txt').read_text(), 'valuable-uncommitted\n')
    s.eq('switch.restored-untracked', (p / 'new.txt').read_text(), 'untracked\n')
    s.eq('stash.apply-retains-save', s.git(p, 'rev-parse', 'refs/stash').strip(), stash)
    s.snapshot(p, 'dirty-switch-refused-and-recovered')


def stash_conflict(s):
    p = s.seeded()
    base = s.head(p)
    s.write(p, 'a.txt', 'saved-index\n')
    s.git(p, 'add', '--', 'a.txt')
    s.write(p, 'a.txt', 'saved-worktree\n')
    s.write(p, 'new.txt', 'saved-untracked\n')
    s.git(p, 'stash', 'push', '-u', '-m', 'Saved three layers')
    saved = s.git(p, 'rev-parse', 'refs/stash').strip()
    s.eq('stash.clean-after-save', s.git(p, 'status', '--porcelain=v1'), '')
    s.write(p, 'a.txt', 'new-base\n')
    s.commit(p, 'Conflicting base', 'a.txt')
    s.git(p, 'stash', 'apply', saved, expected='nonzero')
    s.eq('stash.conflict-present', bool(s.git(p, 'ls-files', '-u')), True)
    if s.mutation == 'drop-save-before-verify':
        s.git(p, 'stash', 'drop', 'stash@{0}')
    s.eq('stash.conflict-save-retained', saved in s.git(p, 'stash', 'list', '--format=%H').splitlines(), True)
    s.eq('stash.saved-worktree-readable', s.git(p, 'show', saved + ':a.txt'), 'saved-worktree\n')
    s.snapshot(p, 'stash-application-conflict')
    recovery = s.root / 'recovery'
    s.git(p, 'worktree', 'add', '-b', 'recovery/stash', str(recovery), base)
    s.repos.append((recovery, False))
    s.git(recovery, 'stash', 'apply', '--index', saved)
    s.eq('stash.recovered-index', s.git(recovery, 'show', ':a.txt'), 'saved-index\n')
    s.eq('stash.recovered-worktree', (recovery / 'a.txt').read_text(), 'saved-worktree\n')
    s.eq('stash.recovered-untracked', (recovery / 'new.txt').read_text(), 'saved-untracked\n')
    s.snapshot(recovery, 'stash-three-layers-recovered-without-dropping')
    s.write(p, 'a.txt', 'new-base\nsaved-worktree\n')
    s.commit(p, 'Resolve saved work against new base', 'a.txt', 'new.txt')
    s.eq('stash.resolution-has-both', s.git(p, 'show', 'HEAD:a.txt'), 'new-base\nsaved-worktree\n')
    s.eq('stash.save-still-present-after-resolution', s.git(p, 'rev-parse', 'refs/stash').strip(), saved)


def worktree(s):
    p = s.seeded()
    s.eq('branch.valid-name', s.git(p, 'check-ref-format', '--branch', 'feature/parser').strip(), 'feature/parser')
    s.git(p, 'check-ref-format', '--branch', 'feature..parser', expected='nonzero')
    before = s.state(p)
    duplicate = s.root / 'duplicate'
    if s.mutation == 'force-duplicate-worktree':
        s.git(p, 'worktree', 'add', '--force', str(duplicate), 'main')
    else:
        s.git(p, 'worktree', 'add', str(duplicate), 'main', expected='nonzero')
    s.eq('worktree.duplicate-path-not-created', duplicate.exists(), False)
    q = s.root / 'topic'
    s.git(p, 'worktree', 'add', '-b', 'feature/parallel', str(q), 'HEAD')
    s.repos.append((q, False))
    s.write(q, 'a.txt', 'parallel\n')
    s.git(q, 'add', '--', 'a.txt')
    s.eq('worktree.independent-index', s.git(p, 'show', ':a.txt'), 'base\n')
    s.git(p, 'worktree', 'remove', str(q), expected='nonzero')
    s.eq('worktree.dirty-removal-preserves', (q / 'a.txt').read_text(), 'parallel\n')
    s.git(q, 'commit', '-m', 'Parallel content')
    tip = s.head(q)
    s.snapshot(q, 'independent-head-and-index')
    s.git(p, 'worktree', 'remove', str(q))
    s.eq('worktree.clean-removed', q.exists(), False)
    s.eq('worktree.branch-retained', s.git(p, 'rev-parse', 'feature/parallel').strip(), tip)
    detached = s.root / 'detached'
    s.git(p, 'worktree', 'add', '--detach', str(detached), 'HEAD')
    s.repos.append((detached, False))
    s.git(detached, 'symbolic-ref', '-q', 'HEAD', expected=1)
    s.eq('worktree.main-unchanged', s.state(p), before)
    s.git(p, 'worktree', 'remove', str(detached))
    s.snapshot(p, 'duplicate-refusal-and-detached-neighbor')


def remote_pair(s):
    bare = s.init('remote.git', bare=True)
    a = s.clone(bare, 'author')
    s.write(a, 'a.txt', 'base\n')
    s.write(a, 'b.txt', 'base-b\n')
    s.commit(a, 'Base content', 'a.txt', 'b.txt')
    s.git(a, 'push', 'origin', 'HEAD:refs/heads/main')
    b = s.clone(bare, 'peer')
    s.eq('clone.checked-out-tip', s.head(b), s.head(a))
    return bare, a, b


def fetch_ff(s):
    bare, a, b = remote_pair(s)
    s.write(b, 'a.txt', 'local-uncommitted\n')
    s.git(b, 'add', '--', 'a.txt')
    s.write(b, 'a.txt', 'later-local\n')
    before = s.state(b)
    s.write(a, 'b.txt', 'remote-one\n')
    remote_one = s.commit(a, 'Remote forward', 'b.txt')
    s.git(a, 'push', 'origin', 'HEAD:refs/heads/main')
    s.git(b, 'fetch', '--no-tags', '--no-recurse-submodules', 'origin',
          'refs/heads/main:refs/remotes/origin/main')
    s.eq('fetch.worktree-index-head-unchanged', s.state(b), before)
    s.eq('fetch.tracking-ref-updated', s.git(b, 'rev-parse', 'origin/main').strip(), remote_one)
    s.git(b, 'stash', 'push', '-m', 'Before fast forward')
    s.git(b, 'pull', '--ff-only', '--no-recurse-submodules', 'origin', 'main')
    s.eq('pull.fast-forward-tip', s.head(b), remote_one)
    s.eq('pull.fast-forward-content', (b / 'b.txt').read_text(), 'remote-one\n')
    s.write(b, 'a.txt', 'local-commit\n')
    local = s.commit(b, 'Local diverging commit', 'a.txt')
    s.write(a, 'b.txt', 'remote-two\n')
    remote_two = s.commit(a, 'Remote diverging commit', 'b.txt')
    s.git(a, 'push', 'origin', 'HEAD:refs/heads/main')
    before = s.state(b)
    if s.mutation == 'pull-merge-instead-of-ff':
        s.git(b, 'pull', '--no-rebase', '--no-edit', '--no-recurse-submodules', 'origin', 'main')
    else:
        s.git(b, 'pull', '--ff-only', '--no-recurse-submodules', 'origin', 'main', expected='nonzero')
    s.eq('pull.ff-rejection-preserves-local-state', s.state(b), before)
    s.eq('pull.failed-integration-still-fetched', s.git(b, 'rev-parse', 'origin/main').strip(), remote_two)
    s.eq('pull.diverged-graph', s.git(b, 'rev-list', '--left-right', '--count', 'HEAD...origin/main').split(), ['1', '1'])
    s.eq('pull.local-tip-not-dropped', s.head(b), local)
    s.snapshot(b, 'fetch-then-ff-only-refusal')


def diverged(s):
    p = s.seeded()
    base = s.head(p)
    s.git(p, 'switch', '-c', 'feature/topic')
    s.write(p, 'a.txt', 'topic\n')
    topic = s.commit(p, 'Topic side', 'a.txt')
    s.git(p, 'switch', 'main')
    s.write(p, 'a.txt', 'main\n')
    main = s.commit(p, 'Main side', 'a.txt')
    return p, base, main, topic


def merge_conflict(s):
    p, base, main, topic = diverged(s)
    before = s.state(p)
    s.git(p, 'merge', '--no-ff', '--no-commit', 'feature/topic', expected='nonzero')
    for stage, content in ((1, 'base\n'), (2, 'main\n'), (3, 'topic\n')):
        s.eq(f'merge.stage-{stage}', s.git(p, 'show', f':{stage}:a.txt'), content)
    s.eq('merge.head-unmoved-during-conflict', s.head(p), main)
    s.eq('merge.second-parent-recorded', s.git(p, 'rev-parse', 'MERGE_HEAD').strip(), topic)
    s.snapshot(p, 'merge-conflict-three-index-stages')
    s.git(p, 'merge', '--abort')
    s.eq('merge.abort-restores-state', s.state(p), before)
    s.git(p, 'rev-parse', '--verify', 'MERGE_HEAD', expected='nonzero')
    s.git(p, 'merge', '--no-ff', '--no-commit', 'feature/topic', expected='nonzero')
    s.write(p, 'a.txt', 'main\n' if s.mutation == 'merge-ours-only' else 'main\ntopic\n')
    s.git(p, 'add', '--', 'a.txt')
    s.eq('merge.no-unmerged-paths', s.git(p, 'ls-files', '-u'), '')
    s.git(p, 'merge', '--continue')
    s.eq('merge.two-parents', s.git(p, 'show', '-s', '--format=%P', 'HEAD').split(), [main, topic])
    s.eq('merge.resolved-content', s.git(p, 'show', 'HEAD:a.txt'), 'main\ntopic\n')
    s.snapshot(p, 'merge-resolved')


def rebase_conflict(s):
    p, base, main, topic = diverged(s)
    s.git(p, 'switch', 'feature/topic')
    s.git(p, 'branch', 'backup/topic-before-rebase', topic)
    before = s.state(p)
    s.git(p, 'rebase', 'main', expected='nonzero')
    s.eq('rebase.temporary-head', s.head(p), main)
    s.eq('rebase.ours-is-new-base', s.git(p, 'show', ':2:a.txt'), 'main\n')
    s.eq('rebase.theirs-is-replayed-topic', s.git(p, 'show', ':3:a.txt'), 'topic\n')
    s.snapshot(p, 'rebase-conflict')
    s.git(p, 'rebase', '--abort')
    s.eq('rebase.abort-restores-state', s.state(p), before)
    s.eq('rebase.abort-restores-branch', s.git(p, 'symbolic-ref', 'HEAD').strip(), 'refs/heads/feature/topic')
    s.git(p, 'rebase', 'main', expected='nonzero')
    if s.mutation == 'skip-conflicting-commit':
        s.git(p, 'rebase', '--skip')
    else:
        s.write(p, 'a.txt', 'main\ntopic\n')
        s.git(p, 'add', '--', 'a.txt')
        s.git(p, 'rebase', '--continue')
    s.eq('rebase.replayed-content-not-skipped', s.git(p, 'show', 'HEAD:a.txt'), 'main\ntopic\n')
    s.eq('rebase.new-commit-id', s.head(p) != topic, True)
    s.eq('rebase.parent-is-new-base', s.git(p, 'show', '-s', '--format=%P', 'HEAD').strip(), main)
    s.eq('rebase.backup-preserves-old-tip', s.git(p, 'rev-parse', 'backup/topic-before-rebase').strip(), topic)
    s.snapshot(p, 'rebase-resolved-with-old-tip-reachable')


def revert_tag(s):
    p = s.seeded()
    base = s.head(p)
    s.git(p, 'tag', '-a', 'v0.1.0', '-m', 'Synthetic candidate', base)
    tag = s.git(p, 'rev-parse', 'refs/tags/v0.1.0').strip()
    s.eq('tag.annotated-object', s.git(p, 'cat-file', '-t', tag).strip(), 'tag')
    s.eq('tag.peeled-candidate', s.git(p, 'rev-parse', 'v0.1.0^{commit}').strip(), base)
    s.write(p, 'a.txt', 'bad\n')
    bad = s.commit(p, 'Incorrect change', 'a.txt')
    if s.mutation == 'move-existing-tag':
        s.git(p, 'tag', '-f', '-a', 'v0.1.0', '-m', 'Attempt replacement', bad)
    else:
        s.git(p, 'tag', '-a', 'v0.1.0', '-m', 'Attempt replacement', bad, expected='nonzero')
    s.eq('tag.duplicate-refusal-unchanged', s.git(p, 'rev-parse', 'refs/tags/v0.1.0').strip(), tag)
    if s.mutation == 'reset-shared-instead-of-revert':
        s.git(p, 'reset', '--hard', base)
    else:
        s.git(p, 'revert', '--no-edit', bad)
    reverted = s.head(p)
    s.eq('revert.distinct-id', reverted not in (base, bad), True)
    s.eq('revert.new-child-not-history-rewrite', s.git(p, 'rev-parse', 'HEAD^').strip(), bad)
    s.eq('revert.bad-commit-retained', s.git(p, 'merge-base', '--is-ancestor', bad, 'HEAD'), '')
    s.eq('revert.restored-content', (p / 'a.txt').read_text(), 'base\n')
    s.write(p, 'a.txt', 'newer\n')
    s.commit(p, 'Newer change', 'a.txt')
    before = s.state(p)
    s.git(p, 'revert', '--no-edit', bad, expected='nonzero')
    s.eq('revert.conflict-present', bool(s.git(p, 'ls-files', '-u')), True)
    s.snapshot(p, 'revert-conflict')
    s.git(p, 'revert', '--abort')
    s.eq('revert.abort-restores-state', s.state(p), before)
    s.git(p, 'commit', '-m', 'Empty operation', expected='nonzero')
    s.eq('commit.failed-empty-preserves-state', s.state(p), before)
    s.snapshot(p, 'revert-and-tag-preserve-history')


def push_history(s):
    bare, a, b = remote_pair(s)
    base = s.head(a)
    s.write(a, 'a.txt', 'author-new\n')
    newer = s.commit(a, 'Other writer update', 'a.txt')
    s.git(a, 'push', 'origin', 'HEAD:refs/heads/main')
    s.write(b, 'b.txt', 'peer-new\n')
    peer = s.commit(b, 'Peer update', 'b.txt')
    s.git(b, 'push', 'origin', 'HEAD:refs/heads/main', expected='nonzero')
    s.eq('push.nonff-retains-remote', s.git(bare, 'rev-parse', 'main').strip(), newer)
    s.git(b, 'push', '--force-with-lease=refs/heads/main:' + base,
          'origin', 'HEAD:refs/heads/main', expected='nonzero')
    s.eq('push.stale-lease-retains-remote', s.git(bare, 'rev-parse', 'main').strip(), newer)
    s.git(b, 'fetch', 'origin', 'refs/heads/main:refs/remotes/origin/main')
    s.git(b, 'merge', '--no-ff', '-m', 'Integrate both writers', 'origin/main')
    merged = s.head(b)
    s.git(b, 'push', 'origin', 'HEAD:refs/heads/main')
    s.eq('push.integrated-remote-tip', s.git(bare, 'rev-parse', 'main').strip(), merged)
    s.eq('push.integrated-content-a', s.git(bare, 'show', 'main:a.txt'), 'author-new\n')
    s.eq('push.integrated-content-b', s.git(bare, 'show', 'main:b.txt'), 'peer-new\n')
    s.git(b, 'push', 'origin', newer + ':refs/heads/isolated-demo')
    if s.mutation == 'force-overwrite-shared':
        s.git(b, 'push', '--force', 'origin', peer + ':refs/heads/isolated-demo')
    else:
        s.git(b, 'push', 'origin', peer + ':refs/heads/isolated-demo', expected='nonzero')
    s.eq('push.shared-history-not-overwritten', s.git(bare, 'rev-parse', 'isolated-demo').strip(), newer)
    s.git(b, 'push', 'origin', peer + ':refs/heads/private-demo')
    s.git(b, 'push', '--force-with-lease=refs/heads/private-demo:' + peer,
          'origin', base + ':refs/heads/private-demo')
    s.eq('push.exact-lease-mechanism-neighbor', s.git(bare, 'rev-parse', 'private-demo').strip(), base)
    s.snapshot(b, 'push-refusal-and-integrated-success')


def submodule_pointer(s):
    lib = s.seeded('library')
    lib_tip = s.head(lib)
    p = s.seeded('superproject')
    s.git(p, 'submodule', 'add', lib.as_uri(), 'deps/library')
    s.commit(p, 'Record dependency commit', '.gitmodules', 'deps/library')
    q = s.clone(p, 'consumer')
    s.eq('submodule.gitlink-mode', s.git(q, 'ls-files', '--stage', 'deps/library').split()[0], '160000')
    s.git(q, 'submodule', 'update', '--init', '--checkout', '--', 'deps/library')
    dep = q / 'deps/library'
    s.eq('submodule.pinned-commit', s.head(dep), lib_tip)
    s.git(dep, 'symbolic-ref', '-q', 'HEAD', expected=1)
    s.write(dep, 'a.txt', 'dependency-new\n')
    newer = s.commit(dep, 'Dependency development', 'a.txt')
    s.eq('submodule.superproject-index-still-pinned',
         s.git(q, 'ls-files', '--stage', 'deps/library').split()[1], lib_tip)
    s.eq('submodule.modified-pointer-visible', bool(s.git(q, 'status', '--porcelain=v1')), True)
    s.git(q, 'add', '--', 'deps/library')
    s.eq('submodule.explicit-new-pointer', s.git(q, 'ls-files', '--stage', 'deps/library').split()[1], newer)
    s.snapshot(q, 'gitlink-is-not-dependency-file-content')


SCENARIOS = {
    'index_snapshot': index_snapshot, 'ignore_rules': ignore_rules,
    'dirty_switch': dirty_switch, 'stash_conflict': stash_conflict,
    'worktree': worktree, 'fetch_ff': fetch_ff,
    'merge_conflict': merge_conflict, 'rebase_conflict': rebase_conflict,
    'revert_tag': revert_tag, 'push_history': push_history,
    'submodule_pointer': submodule_pointer,
}
MUTATIONS = {
    'commit-all': ('index_snapshot', 'index.commit-uses-reviewed-index'),
    'force-add-ignored': ('ignore_rules', 'ignore.excluded-not-staged'),
    'pull-merge-instead-of-ff': ('fetch_ff', 'pull.ff-rejection-preserves-local-state'),
    'skip-conflicting-commit': ('rebase_conflict', 'rebase.replayed-content-not-skipped'),
    'force-overwrite-shared': ('push_history', 'push.shared-history-not-overwritten'),
    'restore-worktree-instead-of-index': ('index_snapshot', 'restore.unstage-preserves-worktree'),
    'drop-save-before-verify': ('stash_conflict', 'stash.conflict-save-retained'),
    'force-duplicate-worktree': ('worktree', 'worktree.duplicate-path-not-created'),
    'merge-ours-only': ('merge_conflict', 'merge.resolved-content'),
    'reset-shared-instead-of-revert': ('revert_tag', 'revert.distinct-id'),
    'move-existing-tag': ('revert_tag', 'tag.duplicate-refusal-unchanged'),
}


def run_scenario(name, *, evidence_parent=None, mutation=None, min_free_bytes=0):
    if name not in SCENARIOS:
        raise ValueError('unknown scenario: ' + name)
    if mutation is not None and (mutation not in MUTATIONS or MUTATIONS[mutation][0] != name):
        raise ValueError('mutation does not target this scenario')
    parent = Path(evidence_parent or tempfile.gettempdir()).resolve()
    available = shutil.disk_usage(parent).free
    if available < min_free_bytes + 8 * 1024 * 1024:
        raise RuntimeError('insufficient free space for a bounded synthetic run')
    evidence = Path(tempfile.mkdtemp(prefix='pg-git-' + name + '-', dir=parent))
    root = evidence / 'sandbox'
    root.mkdir()
    s = Sandbox(root, mutation)
    result = {'schema_version': 1, 'scenario': name, 'mutation': mutation,
              'status': 'running', 'evidence_dir': str(evidence),
              'free_bytes_before': available, 'commands': s.commands,
              'assertions': s.checks, 'snapshots': s.snapshots}
    try:
        result['git_version'] = s.git(root, '--version').strip()
        SCENARIOS[name](s)
        result['status'] = 'passed'
    except Exception as exc:
        result['status'] = 'failed'
        result['error'] = str(exc)
        result['traceback'] = traceback.format_exc()
        # Keep original failed-case files; never copy or overwrite a failed case.
        for repo, bare in s.repos:
            if repo.exists() and not bare:
                try:
                    s.snapshot(repo, 'failure-state')
                except Exception as snapshot_error:
                    result.setdefault('snapshot_errors', []).append(str(snapshot_error))
    if result['status'] == 'passed':
        sandbox = root.resolve()
        if root.is_symlink() or sandbox != evidence.resolve() / 'sandbox':
            raise ValueError('cleanup target must be this run sandbox')
        def remove_readonly(function, path, error):
            if not isinstance(error, PermissionError) or getattr(error, 'winerror', None) != 5:
                raise error
            item = Path(path)
            if not item.resolve().is_relative_to(sandbox):
                raise ValueError('cleanup path escapes this run sandbox')
            mode = item.stat().st_mode
            if mode & stat.S_IWUSR:
                raise error
            item.chmod(mode | stat.S_IWUSR)
            function(path)
        try:
            shutil.rmtree(sandbox, onexc=remove_readonly)
        except OSError as error:
            result.update(status='failed', error='sandbox cleanup failed: ' + str(error),
                          traceback=traceback.format_exc())
    result['sandbox_retained'] = root.exists()
    report = evidence / 'result.json'
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result['report_path'] = str(report)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=['all'] + list(SCENARIOS), default='all')
    parser.add_argument('--mutation', choices=list(MUTATIONS))
    parser.add_argument('--evidence-parent', type=Path)
    parser.add_argument('--min-free-bytes', type=int, default=0)
    options = parser.parse_args(argv)
    if options.mutation and options.scenario == 'all':
        parser.error('--mutation requires one --scenario')
    names = list(SCENARIOS) if options.scenario == 'all' else [options.scenario]
    if options.min_free_bytes < 0:
        parser.error('--min-free-bytes must be nonnegative')
    results = []
    for name in names:
        try:
            result = run_scenario(name, evidence_parent=options.evidence_parent,
                                  mutation=options.mutation, min_free_bytes=options.min_free_bytes)
        except (OSError, RuntimeError, ValueError) as exc:
            result = {'scenario': name, 'status': 'not-run', 'reason': str(exc),
                      'commands': [], 'assertions': [], 'snapshots': []}
        results.append(result)
    print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    if any(r['status'] == 'not-run' for r in results):
        return 2
    return 0 if all(r['status'] == 'passed' for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
