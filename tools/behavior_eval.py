"""Freeze, capture and grade optional Agent behavior trials from actual files.

The operator runs the selected Agent separately. This tool neither contacts a
model provider nor grants a sandbox. Semantic judgments remain reviewer-attested.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checks import behavior_cases as case_contracts
from checks import corpus_contract, validation_common
from checks.behavior_cases import (bind_normative_references, digest, load_suites,
                                   read_json, relative_path, require)

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_WORKSPACE_ENTRIES = 256
MAX_WORKSPACE_BYTES = 16 * 1024 * 1024
ORIGINS = {'operator-captured-agent', 'synthetic-fixture'}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def value_digest(value):
    return digest(canonical(value).encode('utf-8'))


def write_json(path, value):
    path = Path(path)
    require(not path.exists() and not path.is_symlink(), 'refusing to overwrite: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def path_inside(root, name):
    root = Path(root).resolve()
    candidate = root / relative_path(name)
    cursor = root
    for part in Path(name).parts:
        cursor /= part
        require(not cursor.is_symlink(), 'symlink in captured path: ' + name)
    require(candidate.resolve().is_relative_to(root), 'path escapes trial')
    return candidate


def read_bytes(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'regular evidence file required: ' + str(path))
    require(path.stat().st_size <= MAX_FILE_BYTES, 'evidence file exceeds finite byte limit')
    raw = path.read_bytes()
    require(len(raw) <= MAX_FILE_BYTES, 'evidence file grew beyond byte limit')
    return raw


def validate_config(config):
    require(type(config) is dict and set(config) == {
        'schema', 'model', 'host', 'executor_id', 'project_instructions', 'tool_configuration',
        'parameters', 'identity_limitations'}, 'execution configuration fields')
    require(config['schema'] == 'standards-behavior-execution/1', 'execution configuration schema')
    for key in ('executor_id', 'project_instructions', 'identity_limitations'):
        require(type(config[key]) is str and config[key].strip(), 'execution configuration text: ' + key)
    require(type(config['model']) is dict and set(config['model']) == {
        'requested_id', 'observed_id', 'identity_source', 'immutable'}, 'model identity fields')
    for key in ('requested_id', 'identity_source'):
        require(type(config['model'][key]) is str and config['model'][key].strip(), 'model identity text')
    require(config['model']['observed_id'] is None or
            (type(config['model']['observed_id']) is str and config['model']['observed_id'].strip()),
            'observed model ID is text or null')
    require(type(config['model']['immutable']) is bool, 'model immutable flag')
    require(not config['model']['immutable'] or config['model']['observed_id'] is not None,
            'an unknown model identity cannot be declared immutable')
    require(type(config['host']) is dict and set(config['host']) == {'name', 'version'}, 'host identity fields')
    for value in config['host'].values():
        require(type(value) is str and value.strip(), 'host identity text')
    require(type(config['tool_configuration']) is dict and type(config['parameters']) is dict,
            'tool configuration and parameters must be objects')
    require(len(canonical(config).encode('utf-8')) <= 65536, 'execution configuration exceeds 64 KiB')
    return config


def grader_identity(root):
    actual = {'tools/behavior_eval.py': Path(__file__),
              'checks/behavior_cases.py': Path(case_contracts.__file__),
              'checks/corpus_contract.py': Path(corpus_contract.__file__),
              'checks/validation_common.py': Path(validation_common.__file__)}
    result = {}
    for name, implementation in actual.items():
        observed = digest(implementation.read_bytes())
        require(digest((Path(root) / name).read_bytes()) == observed,
                'declared source differs from the running grader: ' + name)
        result[name] = observed
    return result


def prepare(root, out, config, selected=None, repetitions=1):
    root = Path(root).resolve()
    out = Path(out).resolve()
    require(not out.is_relative_to(root), 'trial evidence must be outside the source tree')
    require(type(repetitions) is int and 1 <= repetitions <= 20, 'repetitions must be 1..20')
    validate_config(config)
    suites = load_suites(root)
    choices = [(path, suite, case) for path, suite in suites for case in suite['cases']]
    wanted = set(selected) if selected else {case['id'] for _, _, case in choices}
    require(wanted and wanted <= {case['id'] for _, _, case in choices}, 'unknown or empty selected cases')
    require(not out.exists(), 'run directory already exists')
    # All validation precedes writes; only the newly requested run directory is created.
    normative = bind_normative_references(root, suites)
    source_version = read_json(root / 'project.json')['version']
    grader = grader_identity(root)
    out.mkdir(parents=True)
    planned = []
    for source, suite, case in choices:
        if case['id'] not in wanted:
            continue
        for trial in range(1, repetitions + 1):
            relative = case['id'] + '/' + str(trial)
            run = out / relative
            workspace = run / 'workspace'
            workspace.mkdir(parents=True)
            for item in case['setup']:
                target = path_inside(workspace, item['path'])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(item['text'], encoding='utf-8')
            plan = {
                'schema': 'standards-behavior-plan/1', 'case_id': case['id'], 'trial': trial,
                'case': case, 'case_sha256': value_digest(case),
                'suite_path': source.relative_to(root).as_posix(), 'suite_sha256': digest(source.read_bytes()),
                'source_release': source_version, 'normative_bindings': normative,
                'grader_identity': grader, 'execution_config': config,
                'execution_config_sha256': value_digest(config),
                'identity_assurance': 'operator-declared; provenance requires independent review',
                'maximum_evidence_file_bytes': MAX_FILE_BYTES}
            write_json(run / 'plan.json', plan)
            (run / 'prompt.txt').write_text(case['prompt'] + '\n', encoding='utf-8')
            planned.append({'case_id': case['id'], 'trial': trial, 'directory': relative,
                            'plan_sha256': digest((run / 'plan.json').read_bytes())})
    batch = {'schema': 'standards-behavior-batch/1', 'source_release': source_version,
             'execution_config_sha256': value_digest(config), 'planned': planned,
             'success_policy': 'all-selected-trials-pass; no missing or fixture trials count as success',
             'scope': 'selected cases and declared runtime; no family-wide compatibility claim'}
    write_json(out / 'batch.json', batch)
    return {'planned': len(planned), 'batch_sha256': digest((out / 'batch.json').read_bytes()), 'directory': str(out)}


def validate_plan(root, run):
    root, run = Path(root).resolve(), Path(run).resolve()
    plan = read_json(run / 'plan.json')
    require(plan.get('schema') == 'standards-behavior-plan/1', 'plan schema')
    validate_config(plan['execution_config'])
    require(value_digest(plan['execution_config']) == plan['execution_config_sha256'], 'configuration drift')
    suites = load_suites(root)
    source = path_inside(root, plan['suite_path'])
    require(digest(source.read_bytes()) == plan['suite_sha256'], 'case suite changed; use original source version')
    matches = [case for path, suite in suites if path.resolve() == source.resolve()
               for case in suite['cases'] if case['id'] == plan['case_id']]
    require(len(matches) == 1 and value_digest(plan['case']) == plan['case_sha256'] and
            value_digest(matches[0]) == plan['case_sha256'],
            'case contract drift')
    require(plan['normative_bindings'] == bind_normative_references(root, suites), 'normative binding drift')
    require(plan['grader_identity'] == grader_identity(root), 'grader changed; use original source version')
    require(plan['source_release'] == read_json(root / 'project.json')['version'], 'source release drift')
    require((run / 'prompt.txt').read_text(encoding='utf-8') == plan['case']['prompt'] + '\n', 'task prompt drift')
    return plan


def snapshot(run, case):
    run = Path(run)
    workspace = run / 'workspace'
    require(workspace.is_dir() and not workspace.is_symlink(), 'regular trial workspace required')
    names = {item['path'] for item in case['setup']} | {item['path'] for item in case['checks']}
    for directory, dirs, files in os.walk(workspace, followlinks=False):
        for entry in dirs + files:
            path = Path(directory) / entry
            name = path.relative_to(workspace).as_posix()
            path_inside(workspace, name)
            names.add(name)
            require(len(names) <= MAX_WORKSPACE_ENTRIES, 'workspace entry limit exceeded')
    result = {}
    total = 0
    for name in sorted(names):
        path = path_inside(workspace, name)
        if not path.exists():
            result[name] = {'exists': False}
        elif path.is_dir():
            result[name] = {'exists': True, 'kind': 'directory'}
        else:
            raw = read_bytes(path)
            total += len(raw)
            require(total <= MAX_WORKSPACE_BYTES, 'workspace byte limit exceeded')
            result[name] = {'exists': True, 'bytes': len(raw), 'sha256': digest(raw)}
    return result


def capture(root, run, response, trace, origin, status='completed', exit_code=0):
    run = Path(run).resolve()
    plan = validate_plan(root, run)
    require(origin in ORIGINS, 'capture origin')
    require(status in {'completed', 'timeout', 'error'}, 'execution status')
    require(type(exit_code) is int and -255 <= exit_code <= 255, 'exit code')
    require(not (run / 'observation.json').exists(), 'capture already exists; keep original evidence')
    for name in ('response.txt', 'trace.txt'):
        require(not (run / name).exists(), 'capture target already exists')
    response_raw, trace_raw = read_bytes(response), read_bytes(trace)
    response_raw.decode('utf-8')
    trace_raw.decode('utf-8')
    require(trace_raw.strip(), 'visible execution record required')
    artifacts = snapshot(run, plan['case'])
    with (run / 'response.txt').open('xb') as stream:
        stream.write(response_raw)
    with (run / 'trace.txt').open('xb') as stream:
        stream.write(trace_raw)
    observation = {
        'schema': 'standards-behavior-observation/1', 'case_id': plan['case_id'],
        'trial': plan['trial'], 'plan_sha256': digest((run / 'plan.json').read_bytes()),
        'origin': origin, 'execution_status': status, 'exit_code': exit_code,
        'response_sha256': digest(response_raw), 'trace_sha256': digest(trace_raw),
        'artifacts': artifacts, 'provenance': 'operator capture; hashes establish identity, not authenticity'}
    write_json(run / 'observation.json', observation)
    return {'observation_sha256': digest((run / 'observation.json').read_bytes()), 'artifacts': len(artifacts)}


def equal_json(actual, expected):
    if type(actual) is bool or type(expected) is bool:
        return type(actual) is type(expected) and actual == expected
    if type(actual) in (int, float) and type(expected) in (int, float):
        return actual == expected
    if type(actual) is not type(expected):
        return False
    if type(actual) is dict:
        return actual.keys() == expected.keys() and all(equal_json(actual[k], expected[k]) for k in actual)
    if type(actual) is list:
        return len(actual) == len(expected) and all(equal_json(a, b) for a, b in zip(actual, expected))
    return actual == expected


def artifact_check(run, check):
    try:
        path = path_inside(Path(run) / 'workspace', check['path'])
        if check['kind'] == 'absent':
            passed = not path.exists()
        elif check['kind'] == 'exists':
            read_bytes(path)
            passed = True
        else:
            raw = read_bytes(path)
            text = raw.decode('utf-8')
            if check['kind'] == 'text_contains':
                passed = check['expected'] in text
            elif check['kind'] == 'text_excludes':
                passed = check['expected'] not in text
            elif check['kind'] == 'text_equals':
                passed = text == check['expected']
            elif check['kind'] == 'json_equals':
                passed = equal_json(read_json(path), check['expected'])
            else:
                raise ValueError('unknown check')
        return {'id': check['id'], 'path': check['path'], 'result': 'PASS' if passed else 'FAIL'}
    except (ValueError, OSError, UnicodeError, RecursionError) as exc:
        return {'id': check['id'], 'path': check['path'], 'result': 'FAIL', 'reason': str(exc)}


def review_template(run):
    run = Path(run)
    plan = read_json(run / 'plan.json')
    require((run / 'observation.json').is_file(), 'capture before review')
    result = {
        'schema': 'standards-behavior-review/1', 'plan_sha256': digest((run / 'plan.json').read_bytes()),
        'observation_sha256': digest((run / 'observation.json').read_bytes()),
        'reviewer_id': '', 'independence_reason': '',
        'provenance': {'judgment': 'unknown', 'reason': '', 'evidence': []},
        'rubric': [{'id': row['id'], 'judgment': 'unknown', 'reason': '', 'evidence': []}
                   for row in plan['case']['rubric']]}
    return result


def check_review_evidence(run, references):
    require(type(references) is list and references, 'review evidence references required')
    for ref in references:
        require(type(ref) is dict and set(ref) == {'path', 'start_line', 'end_line'}, 'review evidence fields')
        name = relative_path(ref['path'])
        require(name in {'response.txt', 'trace.txt', 'observation.json'} or name.startswith('workspace/'),
                'review evidence must refer to captured inputs and outputs')
        path = path_inside(run, name)
        lines = read_bytes(path).decode('utf-8').splitlines()
        start, end = ref['start_line'], ref['end_line']
        require(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines),
                'review evidence line range')


def validate_review(run, plan, review):
    require(type(review) is dict and set(review) == {
        'schema', 'plan_sha256', 'observation_sha256', 'reviewer_id', 'independence_reason',
        'provenance', 'rubric'}, 'review fields')
    require(review['schema'] == 'standards-behavior-review/1', 'review schema')
    require(review['plan_sha256'] == digest((Path(run) / 'plan.json').read_bytes()) and
            review['observation_sha256'] == digest((Path(run) / 'observation.json').read_bytes()),
            'review references stale observation or plan')
    require(type(review['reviewer_id']) is str and review['reviewer_id'].strip() and
            review['reviewer_id'] != plan['execution_config']['executor_id'], 'distinct reviewer identity required')
    require(type(review['independence_reason']) is str and review['independence_reason'].strip(),
            'review independence explanation required')
    expected = [row['id'] for row in plan['case']['rubric']]
    require(type(review['rubric']) is list and [row.get('id') for row in review['rubric']] == expected,
            'review must cover each frozen rubric exactly once')
    rows = [review['provenance'], *review['rubric']]
    for index, row in enumerate(rows):
        require(type(row) is dict and set(row) == ({'judgment', 'reason', 'evidence'} if index == 0 else
                                                 {'id', 'judgment', 'reason', 'evidence'}), 'review row fields')
        require(row['judgment'] in {'pass', 'fail', 'unknown'}, 'review judgment')
        require(type(row['reason']) is str and row['reason'].strip(), 'review rationale required')
        if row['judgment'] != 'unknown':
            check_review_evidence(run, row['evidence'])
    return rows


def evaluate(root, run, review_path=None):
    run = Path(run).resolve()
    plan = validate_plan(root, run)
    result = {'case_id': plan['case_id'], 'trial': plan['trial'], 'result': 'INSUFFICIENT',
              'scope': 'selected case; semantic and provenance conclusions are reviewer-attested'}
    if not (run / 'observation.json').exists():
        return {**result, 'execution': 'not-run', 'reason': 'no captured trial'}
    observation = read_json(run / 'observation.json')
    require(type(observation) is dict and observation.get('schema') == 'standards-behavior-observation/1',
            'observation schema')
    require(observation['plan_sha256'] == digest((run / 'plan.json').read_bytes()) and
            observation['case_id'] == plan['case_id'] and observation['trial'] == plan['trial'], 'observation binding')
    require(observation['origin'] in ORIGINS, 'unknown observation origin')
    require(observation['execution_status'] in {'completed', 'timeout', 'error'} and
            type(observation['exit_code']) is int, 'execution observation status')
    require(digest(read_bytes(run / 'response.txt')) == observation['response_sha256'] and
            digest(read_bytes(run / 'trace.txt')) == observation['trace_sha256'], 'captured evidence changed')
    require(snapshot(run, plan['case']) == observation['artifacts'], 'workspace changed after capture')
    checks = [artifact_check(run, item) for item in plan['case']['checks']]
    require(snapshot(run, plan['case']) == observation['artifacts'], 'workspace changed during grading')
    result.update({'execution': observation['execution_status'], 'origin': observation['origin'], 'checks': checks})
    if any(check['result'] == 'FAIL' for check in checks):
        if observation['origin'] == 'synthetic-fixture':
            return {**result, 'fixture_result': 'FAIL', 'reason': 'synthetic scorer fixture failed; model behavior not run'}
        return {**result, 'result': 'FAIL', 'reason': 'artifact contract failed'}
    if review_path is None or not Path(review_path).is_file():
        reason = ('execution is incomplete or returned an error; independent review missing'
                  if observation['execution_status'] != 'completed' or observation['exit_code'] != 0 else
                  'independent semantic and provenance review missing')
        return {**result, 'reason': reason}
    review = read_json(review_path)
    rows = validate_review(run, plan, review)
    result['review_sha256'] = digest(Path(review_path).read_bytes())
    result['reviewer_id'] = review['reviewer_id']
    if any(row['judgment'] == 'fail' for row in rows):
        if observation['origin'] == 'synthetic-fixture':
            return {**result, 'fixture_result': 'FAIL', 'reason': 'synthetic review fixture failed; model behavior not run'}
        return {**result, 'result': 'FAIL', 'reason': 'semantic or provenance review failed'}
    if observation['execution_status'] != 'completed' or observation['exit_code'] != 0:
        return {**result, 'reason': 'execution is incomplete or returned an error'}
    if any(row['judgment'] == 'unknown' for row in rows):
        return {**result, 'reason': 'semantic or provenance evidence remains unknown'}
    if observation['origin'] == 'synthetic-fixture':
        return {**result, 'fixture_result': 'PASS', 'reason': 'synthetic scorer fixture; model behavior not run'}
    return {**result, 'result': 'PASS', 'reason': 'artifact checks and independent attested review passed'}


def aggregate(root, directory, expected_batch_sha256):
    directory = Path(directory).resolve()
    require(type(expected_batch_sha256) is str and re.fullmatch('[0-9a-f]{64}', expected_batch_sha256),
            'the batch SHA-256 recorded before execution is required')
    require(digest((directory / 'batch.json').read_bytes()) == expected_batch_sha256,
            'batch changed since the recorded pre-execution identity')
    batch = read_json(directory / 'batch.json')
    require(batch.get('schema') == 'standards-behavior-batch/1' and batch.get('planned'), 'batch contract')
    require(type(batch['planned']) is list and len(batch['planned']) <= 720, 'finite planned-trial list')
    rows, identities, groups = [], set(), {}
    for expected in batch['planned']:
        identity = (expected['case_id'], expected['trial'])
        require(identity not in identities, 'duplicate planned trial')
        identities.add(identity)
        run = path_inside(directory, expected['directory'])
        require(digest((run / 'plan.json').read_bytes()) == expected['plan_sha256'], 'frozen plan changed')
        plan = read_json(run / 'plan.json')
        require((plan['case_id'], plan['trial']) == identity and
                plan['execution_config_sha256'] == batch['execution_config_sha256'] and
                plan['source_release'] == batch['source_release'], 'batch plan identity mismatch')
        row = evaluate(root, run, run / 'review.json')
        rows.append(row)
        groups.setdefault(Path(plan['suite_path']).stem, []).append(row)
    counts = {state: sum(row['result'] == state for row in rows) for state in ('PASS', 'FAIL', 'INSUFFICIENT')}
    result = 'FAIL' if counts['FAIL'] else ('INSUFFICIENT' if counts['INSUFFICIENT'] else 'PASS')
    return {'schema': 'standards-behavior-report/1', 'batch_sha256': digest((directory / 'batch.json').read_bytes()),
            'result': result, 'planned': len(rows), 'counts': counts,
            'success_fraction': counts['PASS'] / len(rows), 'trials': rows,
            'by_suite': {name: {'planned': len(items),
                'counts': {state: sum(row['result'] == state for row in items)
                           for state in ('PASS', 'FAIL', 'INSUFFICIENT')}} for name, items in sorted(groups.items())},
            'scope': batch['scope'], 'statistical_claim': 'descriptive selected-trial results only'}


def compare(root, baseline, candidate, baseline_sha256, candidate_sha256):
    before = aggregate(root, baseline, baseline_sha256)
    after = aggregate(root, candidate, candidate_sha256)
    old_batch, new_batch = read_json(Path(baseline) / 'batch.json'), read_json(Path(candidate) / 'batch.json')
    def contracts(directory, batch):
        result = {}
        for row in batch['planned']:
            plan = read_json(Path(directory) / row['directory'] / 'plan.json')
            result[(row['case_id'], row['trial'])] = {key: plan[key] for key in (
                'case_sha256', 'suite_sha256', 'normative_bindings', 'grader_identity')}
        return result
    require(contracts(baseline, old_batch) == contracts(candidate, new_batch),
            'paired comparison requires identical tasks, trials, normative bindings and graders')
    previous = {(row['case_id'], row['trial']): row for row in before['trials']}
    transitions = [{'case_id': row['case_id'], 'trial': row['trial'],
                    'baseline': previous[(row['case_id'], row['trial'])]['result'], 'candidate': row['result']}
                   for row in after['trials']]
    incomplete = before['counts']['INSUFFICIENT'] or after['counts']['INSUFFICIENT']
    return {'schema': 'standards-behavior-comparison/1',
            'status': 'INCOMPLETE' if incomplete else 'DESCRIPTIVE',
            'baseline_batch_sha256': baseline_sha256, 'candidate_batch_sha256': candidate_sha256,
            'baseline_counts': before['counts'], 'candidate_counts': after['counts'],
            'success_fraction_delta': after['success_fraction'] - before['success_fraction'],
            'configuration_changed': old_batch['execution_config_sha256'] != new_batch['execution_config_sha256'],
            'transitions': transitions, 'statistical_claim': 'paired descriptive difference; no significance or causality claim'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--config', type=Path, required=True)
    prep.add_argument('--out', type=Path, required=True)
    prep.add_argument('--case', action='append', dest='cases')
    prep.add_argument('--repetitions', type=int, default=1)
    cap = commands.add_parser('capture')
    cap.add_argument('--run', type=Path, required=True)
    cap.add_argument('--response', type=Path, required=True)
    cap.add_argument('--trace', type=Path, required=True)
    cap.add_argument('--origin', choices=sorted(ORIGINS), required=True)
    cap.add_argument('--status', choices=('completed', 'timeout', 'error'), default='completed')
    cap.add_argument('--exit-code', type=int, default=0)
    review = commands.add_parser('review-template')
    review.add_argument('--run', type=Path, required=True)
    ev = commands.add_parser('evaluate')
    ev.add_argument('--run', type=Path, required=True)
    ev.add_argument('--review', type=Path)
    summary = commands.add_parser('aggregate')
    summary.add_argument('--directory', type=Path, required=True)
    summary.add_argument('--batch-sha256', required=True)
    comparison = commands.add_parser('compare')
    comparison.add_argument('--baseline', type=Path, required=True)
    comparison.add_argument('--candidate', type=Path, required=True)
    comparison.add_argument('--baseline-sha256', required=True)
    comparison.add_argument('--candidate-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            result = prepare(args.root, args.out, read_json(args.config), args.cases, args.repetitions)
        elif args.command == 'capture':
            result = capture(args.root, args.run, args.response, args.trace, args.origin, args.status, args.exit_code)
        elif args.command == 'review-template':
            result = review_template(args.run)
        elif args.command == 'evaluate':
            result = evaluate(args.root, args.run, args.review)
        elif args.command == 'aggregate':
            result = aggregate(args.root, args.directory, args.batch_sha256)
        else:
            result = compare(args.root, args.baseline, args.candidate, args.baseline_sha256, args.candidate_sha256)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 1 if result.get('result') == 'FAIL' else (
            2 if result.get('result') == 'INSUFFICIENT' or result.get('status') == 'INCOMPLETE' else 0)
    except (ValueError, OSError, KeyError, TypeError, UnicodeError, RecursionError) as exc:
        print(json.dumps({'result': 'INVALID', 'reason': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
