"""CI gate for the published working-protocol map; standard library only."""
import json
from pathlib import Path
import sys

from policy import ROOT, SOURCES, fingerprints


def check(root=ROOT):
    graph = json.loads((root / 'graphify-out/graph.json').read_text(encoding='utf-8'))
    manifest = json.loads((root / 'graphify-out/protocol_manifest.json').read_text(encoding='utf-8'))
    current = fingerprints()
    if manifest.get('source_hashes') != current:
        raise ValueError('Working-protocol sources changed: rebuild Graphify before publishing')
    ids = {node['id'] for node in graph['nodes']}
    sources = {node.get('source_file') for node in graph['nodes']}
    if not set(current) <= sources:
        raise ValueError('Graph is missing mandatory working-protocol nodes')
    entries = graph.get('protocol_entrypoints', [])
    if (not entries or entries[0].get('source_file') != SOURCES['working_protocol'][0]
            or entries[0].get('priority') != 100 or any(entry.get('id') not in ids for entry in entries)):
        raise ValueError('Graph must prioritize the working protocol')
    print('Graphify protocol map is current; authority, testing, channels and owner opt-ins are indexed.')


if __name__ == '__main__':
    try:
        check()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('Graphify protocol gate failed: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
