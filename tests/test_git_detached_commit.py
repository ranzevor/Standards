"""Git attached/detached HEAD and immutable parent/tree acceptance."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class DetachedCommit(unittest.TestCase):
    def test_attached_and_detached_commit_keep_exact_parent_and_refs(self):
        if shutil.which('git') is None:
            self.skipTest('Git CLI unavailable in this target environment')
        with tempfile.TemporaryDirectory() as directory:
            repo=Path(directory)
            env=os.environ.copy()
            env.update({'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,
                        'GIT_AUTHOR_NAME':'Standards Test','GIT_COMMITTER_NAME':'Standards Test',
                        'GIT_AUTHOR_EMAIL':'standards@example.invalid',
                        'GIT_COMMITTER_EMAIL':'standards@example.invalid',
                        'GIT_TERMINAL_PROMPT':'0'})
            def git(*args):
                run=subprocess.run(['git','-C',str(repo),*args],env=env,
                                   capture_output=True,text=True,timeout=20)
                self.assertEqual(run.returncode,0,run.stderr)
                return run.stdout.strip()
            git('init','-b','main')
            (repo/'record.txt').write_text('root\n',encoding='utf-8')
            git('add','record.txt');git('commit','-m','initial')
            initial=git('rev-parse','HEAD')
            (repo/'record.txt').write_text('attached\n',encoding='utf-8')
            git('add','record.txt');git('commit','-m','attached')
            attached=git('rev-parse','HEAD')
            self.assertNotEqual(attached,initial)
            self.assertEqual(git('rev-parse','main'),attached)
            self.assertEqual(git('rev-parse','HEAD^'),initial)
            self.assertEqual(git('cat-file','-p',attached).split('\n')[0],
                             'tree '+git('rev-parse','HEAD^{tree}'))
            git('checkout','--detach',attached)
            (repo/'record.txt').write_text('detached\n',encoding='utf-8')
            git('add','record.txt');git('commit','-m','detached')
            detached=git('rev-parse','HEAD')
            self.assertNotEqual(detached,attached)
            self.assertEqual(git('rev-parse','HEAD^'),attached)
            self.assertEqual(git('rev-parse','main'),attached)
            self.assertEqual(git('rev-parse','HEAD'),detached)
            self.assertEqual(git('rev-parse','--abbrev-ref','HEAD'),'HEAD')
            self.assertNotEqual(git('rev-parse','HEAD^{tree}'),git('rev-parse','main^{tree}'))
            git('branch','keep-detached',detached)
            self.assertEqual(git('rev-parse','keep-detached'),detached)
            self.assertEqual(git('show','HEAD:record.txt'),'detached')
            self.assertEqual(git('show','main:record.txt'),'attached')
