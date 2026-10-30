"""Validate the published Standards corpus and its product indexes."""
import argparse
import json
from pathlib import Path
import sys

if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks.core_contract import validate


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=p.parse_args(argv)
    print(json.dumps(validate(args.root),ensure_ascii=False,sort_keys=True))
    return 0

if __name__=='__main__':raise SystemExit(main())
