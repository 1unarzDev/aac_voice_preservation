"""Where recorded input paths live in this repository.

Several frozen manifests (story/example manifests, freeze manifests, evidence archives) record SHA-256
hashes under the working paths the files had when they were produced. Those files are published here as
byte-identical copies under analysis/, so every recorded hash still verifies. `resolve()` maps a recorded
path to its published location; paths not listed are unchanged.

Archived generator scripts (analysis/examples/*select_story.py, analysis/derived/*mine_hyp.py,
analysis/derived/guard_increment_checks.py) are kept byte-exact so their recorded hashes verify; they
resolve the repository root relative to their original location and are provenance records, not entry points.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# recorded path -> published path (byte-identical copy)
RECORDED = {
    'ideas/cycles/c1/hyp_checks.json': 'analysis/derived/main1_hyp_checks.json',
    'ideas/cycles/c1/mine_hyp.py': 'analysis/derived/main1_mine_hyp.py',
    'ideas/cycles/c1/hyp_examples.json': 'analysis/examples/main1_hyp_examples.json',
    'ideas/cycles/c1/story_evidence.json': 'analysis/examples/main1_story_evidence.json',
    'ideas/cycles/c1/select_story.py': 'analysis/examples/main1_select_story.py',
    'ideas/cycles/c2/hyp_checks.json': 'analysis/derived/r2_hyp_checks.json',
    'ideas/cycles/c2/hyp_examples.json': 'analysis/derived/r2_hyp_examples.json',
    'ideas/cycles/c2/mine_hyp.py': 'analysis/derived/r2_mine_hyp.py',
    'ideas/cycles/c2/supplied_sets.csv': 'analysis/derived/r2_supplied_sets.csv',
    'ideas/cycles/c2/cue_source_audit.csv': 'analysis/derived/wb_cue_source_audit.csv',
    'ideas/cycles/c3/story_evidence.json': 'analysis/examples/story_evidence.v1.json',
    'ideas/cycles/c3/story_evidence.v2.json': 'analysis/examples/story_evidence.v2.json',
    'ideas/cycles/c3/select_story.py': 'analysis/examples/select_story.py',
    'ideas/cycles/c3/synth_checks.json': 'analysis/derived/guard_increment_checks.json',
    'ideas/cycles/c3/synth_checks.py': 'analysis/derived/guard_increment_checks.py',
    'orchestration/codex_verify_r2.csv': 'analysis/item_verification/verifier_r2.csv',
}

# Published locations used directly by the analysis and paper scripts.
STORY_V1 = 'analysis/examples/story_evidence.v1.json'
STORY_V2 = 'analysis/examples/story_evidence.v2.json'
SELECTOR = 'analysis/examples/select_story.py'
SELECTOR_V1_PATCH = 'analysis/examples/select_story_v1_to_v1.1.patch'
MAIN1_STORY = 'analysis/examples/main1_story_evidence.json'
MAIN1_HYP_EXAMPLES = 'analysis/examples/main1_hyp_examples.json'
MAIN1_HYP_CHECKS = 'analysis/derived/main1_hyp_checks.json'
GUARD_INCREMENT = 'analysis/derived/guard_increment_checks.json'
R2_HYP_CHECKS = 'analysis/derived/r2_hyp_checks.json'
WB_CUE_SOURCE_AUDIT = 'analysis/derived/wb_cue_source_audit.csv'
ITEM_VERIFIER_R2 = 'analysis/item_verification/verifier_r2.csv'


def published(recorded: str) -> str:
    """Published repository-relative path for a recorded path."""
    return RECORDED.get(recorded, recorded)


def resolve(recorded: str) -> Path:
    """Absolute path of the published file for a recorded path."""
    return ROOT / published(recorded)
