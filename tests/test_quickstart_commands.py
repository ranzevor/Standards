"""Run the published quick-start snippets against controlled download fixtures."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def snippet(language):
    text = (ROOT / 'guides/OFFLINE.md').read_text(encoding='utf-8')
    return re.search(r'```' + language + r'\n(.*?)\n```', text, re.S)[1]


def prepare(directory, scenario):
    version = json.loads((ROOT / 'project.json').read_text(encoding='utf-8'))['version']
    assets = directory / 'downloads'
    assets.mkdir()
    markers = directory / 'markers'
    markers.mkdir()
    work = directory / '工作 目录'
    work.mkdir()
    archive = assets / f'Standards-v{version}-source.zip'
    root = f'Standards-v{version}'
    for_step = lambda name, failed: (
        "import os, sys\nfrom pathlib import Path\n"
        f"Path(os.environ['QUICKSTART_MARKERS'], '{name}').write_text('executed')\n"
        f"sys.exit({7 if failed else 0})\n"
    )
    with zipfile.ZipFile(archive, 'w') as out:
        out.writestr(root + '/verify.py', for_step('verify', scenario == 'verify'))
        out.writestr(root + '/source/tools/skill_lookup.py', for_step('lookup', scenario == 'lookup'))
    if scenario == 'extract':
        archive.write_bytes(b'not a ZIP archive')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if scenario == 'digest':
        digest = '0' * 64
    checksum = f'{digest}  {archive.name}\n'
    if scenario == 'duplicate-checksum':
        checksum += checksum
    (assets / 'SHA256SUMS.txt').write_text(checksum, encoding='ascii')
    environment = {**os.environ, 'QUICKSTART_DOWNLOADS': str(assets),
                   'QUICKSTART_MARKERS': str(markers), 'QUICKSTART_SCENARIO': scenario,
                   'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1'}
    return work, markers, environment


class QuickstartCommandsTests(unittest.TestCase):
    scenarios = ('success', 'download-archive', 'download-checksum', 'digest',
                 'extract', 'verify', 'lookup')

    def assert_result(self, scenario, result, markers):
        detail = (result.stdout + result.stderr).decode('utf-8', 'replace')
        self.assertEqual(result.returncode == 0, scenario == 'success', detail)
        self.assertEqual((markers / 'verify').exists(), scenario in {'success', 'verify', 'lookup'}, detail)
        self.assertEqual((markers / 'lookup').exists(), scenario in {'success', 'lookup'}, detail)

    @unittest.skipUnless(os.name == 'posix' and shutil.which('unzip'), 'POSIX shell and unzip required')
    def test_ubuntu_snippet_stops_on_each_failed_stage(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                work, markers, environment = prepare(directory, scenario)
                bin_path = directory / 'bin'
                bin_path.mkdir()
                curl = bin_path / 'curl'
                curl.write_text(
                    f'#!{sys.executable}\n'
                    'import os, shutil, sys\nfrom pathlib import Path\n'
                    "target = sys.argv[sys.argv.index('-o')+1]\n"
                    "kind = 'download-checksum' if target == 'SHA256SUMS.txt' else 'download-archive'\n"
                    "if os.environ['QUICKSTART_SCENARIO'] == kind: sys.exit(28)\n"
                    "shutil.copyfile(Path(os.environ['QUICKSTART_DOWNLOADS']) / Path(target).name, target)\n",
                    encoding='utf-8')
                curl.chmod(0o755)
                environment['PATH'] = str(bin_path) + os.pathsep + environment.get('PATH', '')
                result = subprocess.run(['sh', '-c', snippet('sh')], cwd=work, env=environment,
                                        capture_output=True, timeout=30)
                self.assert_result(scenario, result, markers)

    def test_powershell_snippet_stops_and_restores_working_directory(self):
        shells = [path for name in ('powershell', 'pwsh') if (path := shutil.which(name))]
        if not shells:
            if os.name == 'nt':
                self.fail('Windows acceptance requires a native PowerShell executable')
            self.skipTest('PowerShell is not installed on this OS')
        for shell in shells:
            for scenario in (*self.scenarios, 'duplicate-checksum'):
                with self.subTest(shell=Path(shell).name, scenario=scenario), tempfile.TemporaryDirectory() as temp:
                    directory = Path(temp)
                    work, markers, environment = prepare(directory, scenario)
                    # The fixture substitutes only the network transfer. Extraction,
                    # PowerShell error handling and Python exit codes execute natively.
                    prelude = r'''
$ErrorActionPreference = 'Continue'
function Invoke-WebRequest {
    param([string] $Uri, [string] $OutFile)
    $stage = if ($OutFile -eq 'SHA256SUMS.txt') { 'download-checksum' } else { 'download-archive' }
    if ($env:QUICKSTART_SCENARIO -eq $stage) {
        Write-Error 'Synthetic download failure'
        return
    }
    Copy-Item -LiteralPath (Join-Path $env:QUICKSTART_DOWNLOADS $OutFile) -Destination $OutFile
}
try {
'''
                    suffix = r'''
    exit 0
} catch {
    Write-Output $_
    exit 19
} finally {
    [System.IO.File]::WriteAllText((Join-Path $env:QUICKSTART_MARKERS 'cwd.txt'), (Get-Location).Path)
    [System.IO.File]::WriteAllText((Join-Path $env:QUICKSTART_MARKERS 'preference.txt'), [string]$ErrorActionPreference)
}
'''
                    script = directory / 'quickstart.ps1'
                    script.write_text(prelude + snippet('powershell') + suffix, encoding='utf-8-sig')
                    environment['PATH'] = str(Path(sys.executable).parent) + os.pathsep + environment.get('PATH', '')
                    result = subprocess.run([shell, '-NoProfile', '-NonInteractive', '-ExecutionPolicy',
                                             'Bypass', '-File', str(script)], cwd=work, env=environment,
                                            capture_output=True, timeout=60)
                    self.assert_result(scenario, result, markers)
                    self.assertEqual(Path((markers / 'cwd.txt').read_text(encoding='utf-8')), work)
                    self.assertEqual((markers / 'preference.txt').read_text(encoding='utf-8'), 'Continue')


if __name__ == '__main__':
    unittest.main()
