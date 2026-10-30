"""Exercise verified Source/Skill archives in independent Unicode working paths.

Uses Python's standard library, records real subprocess results, and never
installs a personal Skill or publishes artifacts. Run once on each target OS.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.verify_release_bundle import digest_of_file, verify_directory, verify_zip


class ConsumerCheckError(ValueError):
    pass


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    Path(path).write_bytes((json.dumps(value, ensure_ascii=False, indent=2,
                                    sort_keys=True) + '\n').encode('utf-8'))


def require(condition, message):
    if not condition:
        raise ConsumerCheckError(message)


def run(source_archive, skill_archive, evidence_dir):
    source_archive = Path(source_archive).resolve()
    skill_archive = Path(skill_archive).resolve()
    evidence_dir = Path(evidence_dir).resolve()
    project_root = Path(__file__).resolve().parents[1]
    require(not evidence_dir.is_relative_to(project_root),
            'consumer evidence must be outside the reviewed source tree')
    require(not evidence_dir.exists(), 'consumer evidence directory already exists')
    evidence_dir.mkdir(parents=True)
    record = {
        'schema': 'standards-offline-consumer-check/1', 'status': 'running',
        'started_at': timestamp(), 'commands': [], 'archives': {},
        'environment': {
            'system': platform.system(), 'platform': platform.platform(),
            'machine': platform.machine(), 'python': sys.version,
            'executable': sys.executable, 'filesystem_encoding': sys.getfilesystemencoding(),
        },
        'scope': 'this native OS, exact supplied archives, independent Source/Skill consumers',
        'other_platforms': 'not-run',
        'network_scope': 'no consumer network operation requested; no OS network-isolation claim',
    }
    report = evidence_dir / 'execution.json'
    write_json(report, record)

    def command(ident, script, arguments, cwd, *, stdio_encoding='utf-8'):
        argv = [sys.executable, '-S', '-X', 'utf8', '-B', str(script), *arguments]
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        environment.pop('PYTHONHOME', None)
        environment.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                           PYTHONIOENCODING=stdio_encoding, PYTHONNOUSERSITE='1')
        row = {'id': ident, 'argv': argv, 'cwd': str(cwd),
               'stdio_environment': stdio_encoding, 'started_at': timestamp()}
        record['commands'].append(row)
        stdout_path = evidence_dir / (ident + '.stdout')
        stderr_path = evidence_dir / (ident + '.stderr')
        try:
            with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
                result = subprocess.run(argv, cwd=cwd, env=environment,
                                        stdout=stdout, stderr=stderr, timeout=180)
            row['exit_code'] = result.returncode
        except (OSError, subprocess.TimeoutExpired) as error:
            row.update(exit_code=None, error=str(error))
            raise ConsumerCheckError('consumer process did not complete: ' + ident) from error
        finally:
            row['finished_at'] = timestamp()
            for label, path in (('stdout', stdout_path), ('stderr', stderr_path)):
                if path.is_file():
                    raw = path.read_bytes()
                    row[label] = {'path': path.name, 'bytes': len(raw),
                                  'sha256': hashlib.sha256(raw).hexdigest()}
            write_json(report, record)
        require(result.returncode == 0, 'consumer command failed: ' + ident + '; see ' + str(stderr_path))
        try:
            return json.loads(stdout_path.read_bytes().decode('utf-8'))
        except (UnicodeError, ValueError) as error:
            raise ConsumerCheckError('consumer did not emit UTF-8 JSON: ' + ident) from error

    try:
        require(sys.version_info >= (3, 12), 'Python 3.12 or later is required')
        for label, archive, kind in (
                ('source', source_archive, 'source'),
                ('agent-skill', skill_archive, 'agent-skill')):
            verified = verify_zip(archive)
            require(verified['kind'] == kind, 'wrong archive kind for ' + label)
            record['archives'][label] = {'path': str(archive), **verified}
        source_identity = record['archives']['source']
        skill_identity = record['archives']['agent-skill']
        for field in ('version', 'current_snapshot_sha256', 'source_tree_sha256'):
            require(source_identity[field] == skill_identity[field],
                    'Source/Skill inputs differ: ' + field)
        record['version'] = source_identity['version']

        # Extraction follows full manifest/path verification, into a new tree.
        # Spaces and non-ASCII characters exercise actual argv/path handling.
        consumers = evidence_dir / '独立 离线消费者'
        extracted = {}
        for label, archive in (('source', source_archive), ('agent-skill', skill_archive)):
            destination = consumers / label
            destination.mkdir(parents=True)
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(destination)
            extracted[label] = destination / record['archives'][label]['root']
            materialized = verify_directory(extracted[label])
            for field in ('kind', 'version', 'current_snapshot_sha256',
                          'source_tree_sha256', 'manifest_sha256'):
                require(materialized[field] == record['archives'][label][field],
                        'archive identity changed during extraction: ' + label)
            require(digest_of_file(archive) == record['archives'][label]['sha256'],
                    'archive bytes changed during extraction: ' + label)
        source_bundle = extracted['source']
        source = source_bundle / 'source'
        skill = extracted['agent-skill']
        require(not (source / '.git').exists(), 'Source consumer must not depend on a Git checkout')
        foreign_cwd = consumers / '无关 工作目录'
        foreign_cwd.mkdir()

        command('source-verify', source_bundle / 'verify.py', [], foreign_cwd)
        command('skill-verify', skill / 'scripts/verify_bundle.py', [], foreign_cwd)
        for ident, relative in (
                ('source-registry', 'checks/generate_registry.py'),
                ('source-index', 'checks/generate_index.py')):
            command(ident, source / relative, ['--check'], foreign_cwd)
        command('source-contracts', source / 'checks/validate_all.py', [], foreign_cwd)

        documents = json.loads((source / 'registry/standards.json').read_bytes())
        clauses = json.loads((source / 'registry/requirements.json').read_bytes())
        document = documents[0]
        clause = next(row for row in clauses if row['document_id'] == document['id'])
        arguments = ['--document-id', document['id'], '--clause-id', clause['clause_id']]
        for ident, script, base in (
                ('source-lookup', source / 'tools/skill_lookup.py', source),
                ('skill-lookup', skill / 'scripts/lookup.py', skill)):
            # Deliberately hostile redirected-output encoding. CLI output must
            # remain valid UTF-8 JSON and preserve the Chinese title/path.
            result = command(ident, script, arguments, foreign_cwd, stdio_encoding='ascii')
            require(result['version'] == record['version'] and result['total'] == 1,
                    'lookup returned the wrong release or result count')
            row = result['results'][0]
            require(row['document_id'] == document['id'] and row['title'] == document['title'] and
                    row['clause_id'] == clause['clause_id'] and
                    row['section_sha256'] == clause['section_sha256'],
                    'lookup output differs from the indexed document/clause')
            path = base / row['path']
            require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == document['sha256'],
                    'lookup path does not identify the expected consumer file')

        # Read-only consumers must not leave unlisted bytecode/cache files or
        # alter any packaged bytes while running from the foreign directory.
        record['post_run_integrity'] = {
            label: verify_directory(root) for label, root in extracted.items()}
        record['status'] = 'pass'
    except Exception as error:
        record.update(status='fail', error={'type': type(error).__name__, 'detail': str(error)})
        raise
    finally:
        record['finished_at'] = timestamp()
        write_json(report, record)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-archive', type=Path, required=True)
    parser.add_argument('--skill-archive', type=Path, required=True)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.source_archive, args.skill_archive, args.evidence_dir)
    except (ValueError, OSError, KeyError, StopIteration, zipfile.BadZipFile) as error:
        print(json.dumps({'status': 'fail', 'error': str(error)}, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps({'status': result['status'], 'version': result['version'],
                      'system': result['environment']['system'],
                      'commands': len(result['commands']),
                      'report': str(args.evidence_dir.resolve() / 'execution.json')},
                     ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
