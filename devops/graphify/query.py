"""Required agent entry point: working protocol first, then source-linked Graphify."""
import argparse
import subprocess
import sys

from policy import ROOT
from check import check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question')
    args = parser.parse_args()
    check()
    print((ROOT / 'docs/WORKING_PROTOCOL.md').read_text(encoding='utf-8'), flush=True)
    return subprocess.run([sys.executable, '-m', 'graphify', 'query', args.question,
                           '--budget', '1500'], cwd=ROOT, timeout=60).returncode


if __name__ == '__main__':
    raise SystemExit(main())
