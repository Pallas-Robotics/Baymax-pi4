"""Source-linked, highest-priority entry points for the project's Graphify map."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    'working_protocol': ('docs/WORKING_PROTOCOL.md', 'START HERE: mandatory working protocol and authority', 100),
    'agent_rules': ('AGENTS.md', 'Mandatory Graphify-first agent instructions', 100),
    'testing_protocol': ('Baymax-main/TESTING_PROTOCOL.md', 'Software, chamber simulation, hardware and release evidence', 100),
    'channel_policy': ('docs/UPDATE_CHANNELS.md', 'Authoritative repository, stable fixes and owner-selected channels', 100),
    'contributing': ('CONTRIBUTING.md', 'Professional feature branches, pull requests and review', 100),
    'readme': ('README.md', 'Which branch and pull request to use', 90),
    'experiments': ('Baymax-main/features/experimental/README.md', 'Owner opt-ins and experimental testing stages', 90),
    'software_stage': ('Baymax-main/features/experimental/tested_in_software/README.md', 'Software testing includes direct Pi injection', 80),
    'sim_stage': ('Baymax-main/features/experimental/tested_in_sim/README.md', 'Simulation means chamber video and audio replay', 80),
    'hardware_stage': ('Baymax-main/features/experimental/tested_in_hardware/README.md', 'Physical hardware trials and lead approval', 80),
}


def fingerprints():
    return {source: hashlib.sha256((ROOT / source).read_text(encoding='utf-8').encode('utf-8')).hexdigest()
            for source, _label, _priority in SOURCES.values()}


def semantic_graph():
    nodes = [{'id': key, 'label': label, 'file_type': 'document', 'source_file': source,
              'source_location': 'document', '_origin': 'semantic', 'priority': priority}
             for key, (source, label, priority) in SOURCES.items()]
    edges = [{'source': 'working_protocol', 'target': key, 'relation': 'requires_reading',
              'confidence': 'EXTRACTED', 'confidence_score': 1,
              'source_file': 'docs/WORKING_PROTOCOL.md', 'source_location': 'Mandatory Graphify entry point for LLM work'}
             for key in SOURCES if key != 'working_protocol']
    return {'nodes': nodes, 'edges': edges}
