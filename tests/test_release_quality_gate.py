"""Main push release gate: exact identity, required jobs and fail-closed states."""
import copy
import unittest

from tools.release_quality_gate import (
    QualityGateError, REQUIRED_JOBS, inspect_main_quality,
    require_main_quality, wait_for_main_quality,
)

COMMIT = 'a' * 40
OTHER = 'b' * 40
RUN_ID = 91


class FakeQualityAPI:
    def __init__(self):
        self.head = COMMIT
        self.run = {
            'id': RUN_ID, 'run_attempt': 1,
            'path': '.github/workflows/quality.yml',
            'event': 'push', 'head_branch': 'main', 'head_sha': COMMIT,
            'repository': {'full_name': 'ranzevor/Standards'},
            'status': 'completed', 'conclusion': 'success',
        }
        self.jobs = [
            {'name': name, 'status': 'completed', 'conclusion': 'success', 'run_id': RUN_ID}
            for name in sorted(REQUIRED_JOBS)
        ]
        self.other_run = None
        self.readback = None
        self.after_jobs = None
        self.requests = []

    def request(self, method, suffix):
        self.requests.append((method, suffix))
        if suffix == '/git/ref/heads/main':
            return {'object': {'sha': self.head}}
        if suffix.startswith('/actions/runs?'):
            runs = ([copy.deepcopy(self.run)] if self.run is not None else [])
            if self.other_run:
                runs.insert(0, copy.deepcopy(self.other_run))
            return {'total_count': len(runs), 'workflow_runs': runs}
        if suffix == f'/actions/runs/{RUN_ID}/jobs?per_page=100':
            if self.after_jobs:
                self.after_jobs(self)
            return {'total_count': len(self.jobs), 'jobs': copy.deepcopy(self.jobs)}
        if suffix == f'/actions/runs/{RUN_ID}':
            return copy.deepcopy(self.readback if self.readback is not None else self.run)
        raise AssertionError((method, suffix))


class QualityGateTests(unittest.TestCase):
    def test_success_requires_same_main_push_and_four_real_jobs(self):
        api = FakeQualityAPI()
        self.assertEqual(require_main_quality(api, COMMIT), RUN_ID)
        self.assertEqual(sum(suffix == '/git/ref/heads/main' for _, suffix in api.requests), 2)
        self.assertTrue(any('/actions/runs?head_sha=' + COMMIT in path for _, path in api.requests))

    def test_no_run_and_unfinished_run_are_pending(self):
        api = FakeQualityAPI()
        api.run = None
        self.assertIsNone(inspect_main_quality(api, COMMIT))
        with self.assertRaisesRegex(QualityGateError, 'has not completed'):
            require_main_quality(api, COMMIT)
        for status in ('queued', 'in_progress', 'waiting', 'pending', 'requested'):
            with self.subTest(status=status):
                api.run = FakeQualityAPI().run
                api.run['status'] = status
                api.run['conclusion'] = None
                self.assertIsNone(inspect_main_quality(api, COMMIT))

    def test_failed_cancelled_skipped_and_neutral_runs_fail(self):
        for conclusion in ('failure', 'cancelled', 'skipped', 'neutral', None):
            with self.subTest(conclusion=conclusion):
                api = FakeQualityAPI()
                api.run['conclusion'] = conclusion
                with self.assertRaises(QualityGateError):
                    require_main_quality(api, COMMIT)

    def test_missing_duplicate_and_unsuccessful_jobs_fail(self):
        for missing in sorted(REQUIRED_JOBS):
            with self.subTest(missing=missing):
                api = FakeQualityAPI()
                api.jobs = [j for j in api.jobs if j['name'] != missing]
                with self.assertRaises(QualityGateError):
                    require_main_quality(api, COMMIT)
        for status, conclusion in (('completed', 'failure'), ('completed', 'skipped'),
                                   ('in_progress', None), ('completed', 'cancelled')):
            with self.subTest(status=status, conclusion=conclusion):
                api = FakeQualityAPI()
                api.jobs[0].update(status=status, conclusion=conclusion)
                with self.assertRaises(QualityGateError):
                    require_main_quality(api, COMMIT)
        api = FakeQualityAPI()
        api.jobs.append(copy.deepcopy(api.jobs[0]))
        with self.assertRaises(QualityGateError):
            require_main_quality(api, COMMIT)
        api = FakeQualityAPI()
        api.jobs[0]['run_id'] = RUN_ID + 1
        with self.assertRaises(QualityGateError):
            require_main_quality(api, COMMIT)

    def test_wrong_branch_event_commit_workflow_repo_or_attempt_fail(self):
        for key, bad in [('head_branch', 'feature'), ('event', 'pull_request'),
                         ('head_sha', OTHER), ('repository', {'full_name': 'elsewhere/Standards'}),
                         ('run_attempt', 0)]:
            with self.subTest(field=key):
                api = FakeQualityAPI()
                api.run[key] = bad
                with self.assertRaises(QualityGateError):
                    inspect_main_quality(api, COMMIT)
        api = FakeQualityAPI()
        api.other_run = {**api.run, 'path': '.github/workflows/release.yml', 'id': 44}
        self.assertEqual(require_main_quality(api, COMMIT), RUN_ID)
        api = FakeQualityAPI()
        api.run['path'] = '.github/workflows/release.yml'
        self.assertIsNone(inspect_main_quality(api, COMMIT))

    def test_main_drift_before_or_during_quality_check(self):
        api = FakeQualityAPI()
        api.head = OTHER
        with self.assertRaisesRegex(QualityGateError, 'main head differs'):
            require_main_quality(api, COMMIT)
        api = FakeQualityAPI()
        api.after_jobs = lambda x: setattr(x, 'head', OTHER)
        with self.assertRaisesRegex(QualityGateError, 'main head differs'):
            require_main_quality(api, COMMIT)

    def test_rerun_or_identity_change_during_readback_fails(self):
        for key, bad in [('run_attempt', 2), ('head_sha', OTHER),
                         ('status', 'in_progress'), ('conclusion', 'failure')]:
            with self.subTest(field=key):
                api = FakeQualityAPI()
                api.readback = {**api.run, key: bad}
                with self.assertRaisesRegex(QualityGateError, 'changed during verification'):
                    require_main_quality(api, COMMIT)

    def test_polling_waits_for_matching_run_and_times_out_closed(self):
        api = FakeQualityAPI()
        api.run['status'] = 'in_progress'
        api.run['conclusion'] = None
        elapsed = [0]
        def advance(seconds):
            elapsed[0] += seconds
            if elapsed[0] >= 10:
                api.run['status'] = 'completed'
                api.run['conclusion'] = 'success'
        self.assertEqual(wait_for_main_quality(api, COMMIT, max_wait_seconds=30,
                                               poll_seconds=5, clock=lambda: elapsed[0],
                                               sleep=advance), RUN_ID)
        api.run = None
        with self.assertRaisesRegex(QualityGateError, 'deadline'):
            wait_for_main_quality(api, COMMIT, max_wait_seconds=0, clock=lambda: 0)

    def test_missing_or_incomplete_pages_fail_closed(self):
        api = FakeQualityAPI()
        api.other_run = copy.deepcopy(api.run)
        with self.assertRaises(QualityGateError):
            require_main_quality(api, COMMIT)
        class Incomplete(FakeQualityAPI):
            def request(self, method, suffix):
                value = super().request(method, suffix)
                if '/actions/runs?' in suffix:
                    value['total_count'] += 1
                return value
        with self.assertRaises(QualityGateError):
            require_main_quality(Incomplete(), COMMIT)


if __name__ == '__main__':
    unittest.main()
