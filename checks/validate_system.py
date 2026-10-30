"""Validate the current normative corpus and its active, reproducible indexes."""
from pathlib import Path
import argparse
import json
import os
import sys
if sys.flags.optimize:
    raise RuntimeError('Standard identity checks require Python without -O/-OO')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks.core_contract import validate as validate_current
ROOT=Path(os.environ.get('STANDARDS_ROOT',Path(__file__).resolve().parents[1])).resolve()

def validate(root=ROOT):
    return validate_current(root)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    print(json.dumps(validate(args.root),ensure_ascii=False,sort_keys=True))
