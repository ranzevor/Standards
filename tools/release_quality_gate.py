"""Require the exact main push quality run before releasing a commit."""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REPOSITORY = 'ranzevor/Standards'
WORKFLOW_PATH = '.github/workflows/quality.yml'
REQUIRED_JOBS = frozenset({
    'contracts',
    'native-consumers / offline-consumer (ubuntu-latest)',
    'native-consumers / offline-consumer (windows-latest)',
    'validate',
})


class QualityGateError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise QualityGateError(message)


def require_main_head(api, commit):
    main = api.request('GET', '/git/ref/heads/main')
    require(isinstance(main, dict) and main.get('object', {}).get('sha') == commit,
            'main head differs from the release source commit')


def inspect_main_quality(api, commit):
    """Return the successful run ID, or None while its exact push run is unfinished."""
    require(isinstance(commit, str) and re.fullmatch(r'[0-9a-f]{40}', commit) is not None,
            'invalid release commit')
    require_main_head(api, commit)
    runs = api.request('GET',
                       f'/actions/runs?head_sha={commit}&event=push&branch=main&per_page=100')
    require(isinstance(runs, dict) and type(runs.get('total_count')) is int
            and isinstance(runs.get('workflow_runs'), list)
            and len(runs['workflow_runs']) == runs['total_count'],
            'incomplete main workflow run listing')
    matches = [run for run in runs['workflow_runs']
               if isinstance(run, dict) and run.get('path') == WORKFLOW_PATH]
    require(len(matches) <= 1, 'ambiguous main quality workflow runs')
    if not matches:
        return None
    run = matches[0]
    require(type(run.get('id')) is int and run['id'] > 0
            and type(run.get('run_attempt')) is int and run['run_attempt'] > 0
            and run.get('event') == 'push' and run.get('head_branch') == 'main'
            and run.get('head_sha') == commit
            and run.get('repository', {}).get('full_name') == REPOSITORY,
            'main quality workflow identity differs')
    if run.get('status') != 'completed':
        require(run.get('status') in {'queued', 'in_progress', 'waiting', 'pending', 'requested'},
                'unknown main quality workflow state')
        return None
    require(run.get('conclusion') == 'success',
            'main quality workflow did not succeed: ' + str(run.get('conclusion')))
    run_id = run['id']
    jobs = api.request('GET', f'/actions/runs/{run_id}/jobs?per_page=100')
    require(isinstance(jobs, dict) and type(jobs.get('total_count')) is int
            and isinstance(jobs.get('jobs'), list)
            and jobs['total_count'] == len(jobs['jobs']),
            'incomplete main quality job listing')
    seen = set()
    for job in jobs['jobs']:
        require(isinstance(job, dict) and isinstance(job.get('name'), str)
                and job['name'] not in seen and job.get('run_id') == run_id,
                'main quality job identity differs or is duplicated')
        seen.add(job['name'])
        require(job.get('status') == 'completed' and job.get('conclusion') == 'success',
                'main quality job did not succeed: ' + job['name'])
    require(REQUIRED_JOBS <= seen,
            'main quality run lacks required contracts, Linux, Windows or validate job')
    observed = api.request('GET', f'/actions/runs/{run_id}')
    require(isinstance(observed, dict)
            and all(observed.get(key) == run.get(key) for key in (
                'id', 'path', 'event', 'head_branch', 'head_sha', 'run_attempt'))
            and observed.get('status') == 'completed'
            and observed.get('conclusion') == 'success',
            'main quality run changed during verification')
    require_main_head(api, commit)
    return run_id


def require_main_quality(api, commit):
    run_id = inspect_main_quality(api, commit)
    require(run_id is not None, 'main quality workflow has not completed successfully')
    return run_id


def wait_for_main_quality(api, commit, max_wait_seconds=1500, poll_seconds=15,
                          clock=time.monotonic, sleep=time.sleep):
    require(0 <= max_wait_seconds <= 3600 and 0 < poll_seconds <= 60,
            'invalid main quality polling limits')
    deadline = clock() + max_wait_seconds
    while True:
        run_id = inspect_main_quality(api, commit)
        if run_id is not None:
            return run_id
        remaining = deadline - clock()
        require(remaining > 0, 'main quality workflow did not complete before the deadline')
        sleep(min(poll_seconds, remaining))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--max-wait-seconds', type=int, default=1500)
    args = parser.parse_args(argv)
    try:
        require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY,
                'unexpected release repository')
        from tools.publish_release import GitHubAPI
        wait_for_main_quality(GitHubAPI(os.environ.get('GH_TOKEN')),
                              args.source_commit, args.max_wait_seconds)
        print('Main quality checks succeeded for the exact release commit.')
        return 0
    except (ValueError, TypeError, OSError) as error:
        print('release quality gate failed: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
