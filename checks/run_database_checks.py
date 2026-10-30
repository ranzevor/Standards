"""Validate current database document bindings and execute the local database tests."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
if sys.flags.optimize: raise RuntimeError('Database checks require normal Python mode')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from checks.repository_registry import validate_entries
from checks.corpus_contract import extract_document
from checks.validation_common import read_json, require


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--evidence-dir', type=Path)
    args = parser.parse_args(argv); root = args.root.resolve()
    if args.evidence_dir is not None:
        require(not args.evidence_dir.resolve().is_relative_to(root), 'execution logs must be outside source')
    entries = [e for e in validate_entries(root) if e['domain'] == 'database']
    indexed = read_json(root/'registry/requirements.json'); count = 0
    for entry in entries:
        actual = extract_document(entry, (root/entry['path']).read_text())['clauses']
        require(actual == [c for c in indexed if c['document_id'] == entry['id']], 'database clause binding drift', entry['id'])
        count += len(actual)
    start = datetime.now(timezone.utc)
    command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_database*.py', '-v']
    result = subprocess.run(command, cwd=root, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'}, capture_output=True, text=True)
    print(result.stdout, end=''); print(result.stderr, end='', file=sys.stderr)
    report = {'started_at': start.isoformat(), 'finished_at': datetime.now(timezone.utc).isoformat(), 'command': command,
              'exit_code': result.returncode, 'python': sys.version, 'sqlite': sqlite3.sqlite_version, 'platform': platform.platform(),
              'documents': len(entries), 'clauses': count, 'stdout': result.stdout, 'stderr': result.stderr,
              'runtime_scope':'local synthetic SQLite and finite database contracts'}
    if args.evidence_dir:
        args.evidence_dir.mkdir(parents=True, exist_ok=True)
        path = args.evidence_dir/('database-run-'+start.strftime('%Y%m%dT%H%M%S.%fZ')+'.json')
        with path.open('x', encoding='utf-8') as stream: json.dump(report, stream, ensure_ascii=False, indent=2)
    require(result.returncode == 0, 'database regression subprocess failed')
    print(json.dumps({'documents': len(entries), 'clauses': count, 'exit_code': result.returncode}))
    return result.returncode

if __name__ == '__main__': raise SystemExit(main())
