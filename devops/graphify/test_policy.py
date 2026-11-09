"""The CI protocol gate rejects missing, stale and deprioritized governance maps."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from check import check
from policy import SOURCES, fingerprints


class ProtocolGateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.out = self.root / 'graphify-out'
        self.out.mkdir()
        self.graph = {'nodes': [{'id': key, 'source_file': value[0]} for key, value in SOURCES.items()],
                      'protocol_entrypoints': [{'id': 'working_protocol', 'source_file': SOURCES['working_protocol'][0], 'priority': 100}]}
        self.hashes = fingerprints()

    def write(self):
        (self.out / 'graph.json').write_text(json.dumps(self.graph), encoding='utf-8')
        (self.out / 'protocol_manifest.json').write_text(json.dumps({'source_hashes': self.hashes}), encoding='utf-8')

    def test_current_map_passes(self):
        self.write()
        with contextlib.redirect_stdout(io.StringIO()):
            check(self.root)

    def test_stale_source_is_rejected(self):
        self.hashes['AGENTS.md'] = 'outdated'
        self.write()
        with self.assertRaisesRegex(ValueError, 'sources changed'):
            check(self.root)

    def test_missing_protocol_node_is_rejected(self):
        self.graph['nodes'] = self.graph['nodes'][1:]
        self.write()
        with self.assertRaisesRegex(ValueError, 'missing mandatory'):
            check(self.root)

    def test_deprioritized_protocol_is_rejected(self):
        self.graph['protocol_entrypoints'] = []
        self.write()
        with self.assertRaisesRegex(ValueError, 'prioritize'):
            check(self.root)

    def test_graphify_may_normalize_a_protocol_node_id(self):
        self.graph['nodes'][0]['id'] = 'docs_working_protocol'
        self.graph['protocol_entrypoints'][0]['id'] = 'docs_working_protocol'
        self.write()
        with contextlib.redirect_stdout(io.StringIO()):
            check(self.root)
