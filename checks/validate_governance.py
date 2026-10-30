"""Current multi-document governance bindings and synthetic project-record semantics."""
import sys
if sys.flags.optimize:raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse,json
from checks.project_governance import ROOT,validate_domain,validate_project
from checks.validation_common import read_json


def validate(root=ROOT):
    root=Path(root).resolve();domain=validate_domain(root)
    record=validate_project(read_json(root/'examples/project-governance/project-record.json'),root)
    return {**domain,'project_record':record,
            'scope':'governance clauses, field conditions, templates and local synthetic project record'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    print(json.dumps(validate(a.root),ensure_ascii=False,sort_keys=True))
