"""Actual subprocess fixture; its protocol is intentionally small and local."""
import json
import os
import sys

def main():
    if sys.flags.optimize:
        sys.stderr.write('optimized entry unsupported\n');return 2
    args=sys.argv[1:]
    if args==['--help']:
        print('fixture: --json -- DATA | --fail | --large');return 0
    if args==['--fail']:
        sys.stderr.write('input rejected\n');return 2
    if args==['--large']:
        for _ in range(64):
            os.write(1,b'x'*8192);os.write(2,b'y'*8192)
        return 0
    if len(args)>=2 and args[:2]==['--json','--']:
        print(json.dumps({'argv':args[2:],'complete':True},ensure_ascii=False));sys.stderr.write('diagnostic\n');return 0
    sys.stderr.write('invalid syntax; no action\n');return 2

if __name__=='__main__':raise SystemExit(main())
