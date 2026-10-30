"""Validate a finite software-repository profile and its local repository contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checks.finite_schema import schema_check
from checks.validation_common import read_json, read_text_exact, require, safe_path, substantive

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'registry/schemas/software-repository-profile.schema.json'
PROFILE = 'governance/software-repository.json'
EXAMPLES = (
    'examples/repository-adoption/public-open-source.json',
    'examples/repository-adoption/private-development.json',
    'examples/repository-adoption/archived-open-source.json',
)
BLOCK_SCALAR = re.compile(r':\s*[|>][0-9+-]*\s*$')
FULL_SHA = re.compile(r'^[0-9a-f]{40}$')
IMAGE_DIGEST = re.compile(r'^docker://.+@sha256:[0-9a-f]{64}$')


def portable_relative(value, label, *, directory=False):
    require(type(value) is str and value.strip() == value and value, label + ' path')
    require('\\' not in value and '\x00' not in value and not re.match(r'^[A-Za-z]:', value),
            label + ' nonportable path', value)
    require(not directory or value.endswith('/'), label + ' directory suffix', value)
    source = value[:-1] if directory else value
    require(source, label + ' empty path', value)
    rel = PurePosixPath(source)
    require(not rel.is_absolute() and '..' not in rel.parts, label + ' path escape', value)
    expected = rel.as_posix() + ('/' if directory else '')
    require(value == expected, label + ' path must use canonical spelling', value, expected)
    return value


def _quoted(text, start, path, line_number):
    quote = text[start]
    value = []
    escaped = False
    index = start + 1
    while index < len(text):
        char = text[index]
        if quote == "'" and char == "'" and index + 1 < len(text) and text[index + 1] == "'":
            value.append("'")
            escaped = True
            index += 2
            continue
        if quote == '"' and char == '\\':
            require(index + 1 < len(text), 'workflow YAML dangling escape', str(path), line_number)
            value.append(text[index + 1])
            escaped = True
            index += 2
            continue
        if char == quote:
            return ''.join(value), index + 1, escaped
        value.append(char)
        index += 1
    require(False, 'workflow YAML multiline or unmatched quote unsupported', str(path), line_number)


def _quote_starts(text, index):
    return index == 0 or text[index - 1].isspace() or text[index - 1] in '[{,:?-'


def _without_comment(line, path, line_number):
    index = 0
    while index < len(line):
        if line[index] in {'"', "'"} and _quote_starts(line, index):
            _, index, _ = _quoted(line, index, path, line_number)
            continue
        if line[index] == '#' and (index == 0 or line[index - 1].isspace()):
            return line[:index]
        index += 1
    return line


def _mapping_at(line, start, path, line_number, *, sequence=False):
    index = start
    while index < len(line) and line[index].isspace():
        index += 1
    if sequence and index < len(line) and line[index] == '-':
        index += 1
        while index < len(line) and line[index].isspace():
            index += 1
    if index < len(line) and line[index] == '?':
        index += 1
        while index < len(line) and line[index].isspace():
            index += 1
    if index >= len(line):
        return None
    if line[index] in {'"', "'"}:
        key, index, _ = _quoted(line, index, path, line_number)
    else:
        match = re.match(r'[A-Za-z_][A-Za-z0-9_-]*', line[index:])
        if match is None:
            return None
        key = match.group(0)
        index += len(key)
    while index < len(line) and line[index].isspace():
        index += 1
    if index >= len(line) or line[index] != ':':
        return None
    return key, index + 1


def _action_scalar(line, start, path, line_number):
    index = start
    while index < len(line) and line[index].isspace():
        index += 1
    require(index < len(line), 'workflow uses value must be an inline scalar', str(path), line_number)
    if line[index] in {'"', "'"}:
        value, end, escaped = _quoted(line, index, path, line_number)
        require(not escaped, 'workflow uses value cannot rely on YAML escapes', str(path), line_number)
        return value, end
    require(line[index] not in {'|', '>', '&', '*', '!', '[', '{'},
            'workflow uses value must be a direct scalar', str(path), line_number)
    end = index
    while end < len(line) and not line[end].isspace() and line[end] not in {',', '}', ']'}:
        end += 1
    require(end > index, 'workflow uses value missing', str(path), line_number)
    return line[index:end], end


def _uses_on_line(line, path, line_number):
    values = []
    first = _mapping_at(line, 0, path, line_number, sequence=True)
    if first is not None and first[0] == 'uses':
        value, _ = _action_scalar(line, first[1], path, line_number)
        values.append(value)
    stack = []
    index = 0
    while index < len(line):
        if line[index] in {'"', "'"} and _quote_starts(line, index):
            _, index, _ = _quoted(line, index, path, line_number)
            continue
        char = line[index]
        if char in {'{', '['}:
            stack.append('}' if char == '{' else ']')
            candidate = _mapping_at(line, index + 1, path, line_number)
            if candidate is not None and candidate[0] == 'uses':
                value, _ = _action_scalar(line, candidate[1], path, line_number)
                values.append(value)
        elif char in {'}', ']'}:
            if stack and stack[-1] == char:
                stack.pop()
        elif char == ',' and stack:
            candidate = _mapping_at(line, index + 1, path, line_number)
            if candidate is not None and candidate[0] == 'uses':
                value, _ = _action_scalar(line, candidate[1], path, line_number)
                values.append(value)
        index += 1
    return values


def workflow_action_values(path):
    values = []
    block_indent = None
    for line_number, raw_line in enumerate(read_text_exact(path).splitlines(), 1):
        require('\t' not in raw_line[:len(raw_line) - len(raw_line.lstrip())],
                'workflow YAML tab indentation unsupported', str(path), line_number)
        indent = len(raw_line) - len(raw_line.lstrip(' '))
        if block_indent is not None:
            if not raw_line.strip() or indent > block_indent:
                continue
            block_indent = None
        line = _without_comment(raw_line, path, line_number)
        if not line.strip():
            continue
        values.extend(_uses_on_line(line, path, line_number))
        if BLOCK_SCALAR.search(line):
            block_indent = indent
    return values


def validate_action_pins(paths):
    checked = 0
    for path in paths:
        for value in workflow_action_values(path):
            if value.startswith('./'):
                continue
            if value.startswith('docker://'):
                require(IMAGE_DIGEST.fullmatch(value) is not None,
                        'workflow container action must use sha256 digest', str(path), value)
            else:
                require('@' in value, 'remote action missing ref', str(path), value)
                action, ref = value.rsplit('@', 1)
                require('/' in action and FULL_SHA.fullmatch(ref) is not None,
                        'remote action must use full commit SHA', str(path), value)
            checked += 1
    return checked


def _markers(path, expected):
    text = read_text_exact(path)
    for marker in expected:
        require(marker in text, 'repository template field missing', path.as_posix(), marker)
    return len(expected)


def validate_template_contracts(root=ROOT):
    root = Path(root).resolve()
    checks = {
        'templates/repository/PULL_REQUEST_TEMPLATE.md': (
            '## 目标、基线与候选', '## 行为与影响', '## 验证', '## 审查与合并前置',
            '作者自查', '独立审查', '恢复/回退', '未执行',
        ),
        'templates/repository/ISSUE_TEMPLATE/defect.md': (
            '## 受影响对象', '## 复现与实际结果', '## 影响与恢复', '## 修复验收', 'SECURITY',
        ),
        'templates/repository/ISSUE_TEMPLATE/proposal.md': (
            '## 目标、对象与非目标', '## 方案与接口影响', '## 失败恢复与迁移',
            '## 可观察验收', '## 来源与未决项',
        ),
        '.github/pull_request_template.md': (
            '## 目标、基线与候选', '## 规范、行为与影响', '## 验证', '## 审查与合并前置',
            '作者自查', '独立审查', '恢复/回退', '未执行',
        ),
        '.github/ISSUE_TEMPLATE/defect.md': (
            '## 对象', '## 可复验事实', '## 影响与边界', '## 建议验收', 'SECURITY',
        ),
        '.github/ISSUE_TEMPLATE/proposal.md': (
            '## 目标与适用对象', '## 现有条款及差异', '## 机制、不变量与失败恢复',
            '## 反例、合法邻例与可观察验收', '## 来源版本、依赖、兼容与未完成项',
        ),
    }
    fields = 0
    for relative, expected in checks.items():
        fields += _markers(safe_path(root, relative), expected)
    return {'templates': len(checks), 'required_fields': fields}


def _profile_paths(profile):
    files = profile['files']
    values = [files['readme']]
    for name in ('license', 'rights', 'contributing', 'security',
                 'pull_request_template', 'platform_controls'):
        if files[name] is not None:
            values.append(files[name])
    values.extend(files['issue_templates'])
    values.extend(files['workflows'])
    return values


def validate_profile(profile, schema, root=None):
    schema_check(profile, schema)
    repository = profile['repository']
    files = profile['files']
    commands = profile['quick_start']['commands']
    exclusions = profile['evidence_exclusions']
    require(len(files['issue_templates']) == len(set(files['issue_templates'])),
            'duplicate issue template path')
    require(len(files['workflows']) == len(set(files['workflows'])),
            'duplicate workflow path')
    require(len(commands) == len(set(commands)), 'duplicate quick-start command')
    require(len(exclusions) == len(set(exclusions)), 'duplicate evidence exclusion')
    for value in _profile_paths(profile):
        portable_relative(value, 'repository file')
    for value in exclusions:
        portable_relative(value, 'evidence exclusion', directory=True)

    if profile['profile_state'] == 'starter':
        require(profile['example_only'] is True
                and repository['distribution'] == 'none'
                and repository['release'] == 'not-published'
                and repository['final_identity'] is None,
                'starter profile cannot claim distribution or release')
        return {'id': profile['id'], 'profile_state': 'starter', 'contract_valid': True}

    require(repository['maintenance'] not in {'active', 'limited'}
            or substantive(repository['maintainer']),
            'active or limited maintenance requires a maintainer')
    require(repository['release'] == 'not-published'
            or substantive(repository['final_identity']),
            'published or withdrawn release requires final identity')
    require(repository['maintenance'] != 'archived'
            or substantive(repository['final_identity']),
            'archived repository requires final identity')
    require(repository['distribution'] != 'open-source' or files['license'] is not None,
            'open-source distribution requires license')
    require(repository['distribution'] != 'source-visible' or files['rights'] is not None,
            'source-visible distribution requires rights status')
    require(not (repository['visibility'] == 'public' and repository['distribution'] == 'none')
            or files['rights'] is not None,
            'public repository without distribution grant requires rights status')
    require(repository['collaboration'] == 'closed'
            or (files['issue_templates'] and files['security'] is not None),
            'issue collaboration requires issue templates and security channel')
    require(repository['collaboration'] != 'contributions'
            or (files['contributing'] is not None and files['pull_request_template'] is not None),
            'contribution collaboration requires contributing and PR templates')
    require(files['platform_controls'] is not None,
            'defined profile requires platform or equivalent controls contract')
    require(repository['maintenance'] not in {'active', 'limited'}
            and repository['release'] != 'published'
            or bool(commands),
            'active, limited or published repository requires quick-start commands')
    require(bool(exclusions), 'defined profile requires evidence exclusions')

    action_count = 0
    tracked_checked = False
    effective_ignore_checked = False
    if root is not None:
        root = Path(root).resolve()
        for value in _profile_paths(profile):
            safe_path(root, value)
        workflow_dir = root / '.github' / 'workflows'
        actual = set()
        if workflow_dir.is_dir():
            actual = {
                path.relative_to(root).as_posix()
                for pattern in ('*.yml', '*.yaml')
                for path in workflow_dir.glob(pattern)
            }
        require(set(files['workflows']) == actual,
                'profile workflow set differs from repository', sorted(actual))
        action_count = validate_action_pins([safe_path(root, value) for value in files['workflows']])
        ignored = {
            line.strip()
            for line in read_text_exact(safe_path(root, '.gitignore')).splitlines()
            if line.strip() and not line.lstrip().startswith('#')
        }
        require(set(exclusions) <= ignored,
                'evidence exclusions missing from .gitignore', sorted(set(exclusions) - ignored))
        if (root / '.git').exists():
            for prefix in exclusions:
                for probe in (prefix, prefix + '.standards-evidence-probe'):
                    ignored_result = subprocess.run(
                        ['git', '-C', str(root), 'check-ignore', '--no-index', '-q', '--', probe],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                    )
                    require(ignored_result.returncode == 0,
                            'evidence exclusion is not effective',
                            probe, ignored_result.stderr.decode('utf-8', errors='replace'))
            effective_ignore_checked = True
            result = subprocess.run(
                ['git', '-C', str(root), 'ls-files', '-z'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            require(result.returncode == 0, 'git tracked-file query failed',
                    result.stderr.decode('utf-8', errors='replace'))
            tracked = result.stdout.decode('utf-8').split('\x00')
            require(not any(path.startswith(prefix) for path in tracked for prefix in exclusions),
                    'tracked implementation evidence violates exclusion')
            tracked_checked = True
    return {
        'id': profile['id'],
        'profile_state': 'defined',
        'contract_valid': True,
        'action_pins_checked': action_count,
        'effective_ignore_checked': effective_ignore_checked,
        'tracked_evidence_checked': tracked_checked,
    }


def validate_current_repository(root=ROOT):
    root = Path(root).resolve()
    schema = read_json(safe_path(root, SCHEMA))
    current = validate_profile(read_json(safe_path(root, PROFILE)), schema, root)
    starter = validate_profile(
        read_json(safe_path(root, 'templates/repository/repository-profile.template.json')),
        schema,
    )
    examples = [
        validate_profile(read_json(safe_path(root, relative)), schema)
        for relative in EXAMPLES
    ]
    templates = validate_template_contracts(root)
    return {
        'current': current,
        'starter': starter,
        'examples': examples,
        'template_contracts': templates,
        'scope': 'finite repository state, local artifacts, workflow pins and evidence exclusions; '
                 'not live platform state, independent review or release acceptance',
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--profile', type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    schema = read_json(safe_path(ROOT, SCHEMA))
    if args.profile:
        require(not args.profile.is_absolute(), 'profile path must be relative to target repository')
        profile_path = safe_path(root, args.profile.as_posix())
    else:
        profile_path = safe_path(root, PROFILE)
    result = validate_profile(read_json(profile_path), schema, root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
