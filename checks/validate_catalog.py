"""Catalogue validation entry point."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checks.validate_system import validate,ROOT
if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    print(json.dumps(validate(a.root),ensure_ascii=False,sort_keys=True))
