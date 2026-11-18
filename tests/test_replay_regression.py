"""Replay regression tests against stored data (CPU only, no API).

1. Judge post-processing: raw per-pass judge responses -> final labels (judge.assemble_rows / judge._final) are replayed
   over the stored judgments of hw1, hw2 and r2c1 and must reproduce the stored final labels (critical, needs_arbiter,
   general dims, general_disagree, added_content). The raw responses are reconstructed from the stored J1_*/J2_* fields
   (pass A carries critical/evidence/general dims, pass B carries added_content/evidence); layer0 labels are the stored L0_*.
2. Input builder golden: the stored request files runs/requests/{hw,r2c,hw2}.jsonl (the request files of runs hw1, r2c1, hw2)
   are rebuilt from their item files with build_requests.build and compared on request_key set, rendered input_text,
   prompt, and target lists.
Plus small synthetic cases of the three _final outcomes (agree / layer0 tiebreak / unresolved).
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import build_requests as B  # noqa: E402
import judge as J  # noqa: E402
import runio  # noqa: E402

GD = J.GENERAL_DIMS
JUDGE_RUNS = ["hw1", "hw2", "r2c1"]
# request file -> (items directory, run it belongs to)
REQUEST_FILES = {"hw": ROOT / "annotation" / "written", "r2c": ROOT / "data" / "items", "hw2": ROOT / "annotation" / "written" / "hw2"}


# ---------------------------------------------------------------------------------------- judge post-processing
def test_final_three_outcomes():
    assert J._final("x", "x") == ("x", False)
    assert J._final("x", "y", "y") == ("y", True)      # layer0 equals one judge: layer0 wins
    assert J._final("x", "y", "x") == ("x", True)
    assert J._final("x", "y", "z") == (None, True)     # layer0 equals neither: unresolved
    assert J._final("x", "y") == (None, True)          # no tiebreak: unresolved


def _raw_from_row(r, v):
    a = {"critical": r[f"{v}_critical"], "evidence": r[f"{v}_evidence"], **{d: r[f"{v}_{d}"] for d in GD}}
    b = {"added_content": r[f"{v}_added_content"], "evidence": r[f"{v}_added_evidence"]}
    return a, b


def _replay(rows):
    junits, res, l0 = [], {v: ({}, {}) for v in ("J1", "J2")}, {}
    for i, r in enumerate(rows):
        u = {k: r[k] for k in ("text_id", "family_id", "input_text", "text", "dimension", "critical_options")}
        u["_ak"] = u["_bk"] = i
        junits.append(u)
        for v in ("J1", "J2"):
            a, b = _raw_from_row(r, v)
            res[v][0][i], res[v][1][i] = a, b
        l0[r["text_id"]] = {d: r[f"L0_{d}"] for d in GD}
    # one layer0 entry per text_id: rows of one text_id carry the same L0 labels
    return J.assemble_rows(junits, res, ["J1", "J2"], l0)


@pytest.mark.parametrize("run", JUDGE_RUNS)
def test_judge_postprocessing_replays_stored_final_labels(run):
    rows = runio.read_jsonl(ROOT / "runs" / run / "judgments.jsonl")
    assert len(rows) > 1000
    got = _replay(rows)
    keys = ["critical", "needs_arbiter", "general_disagree", "added_content"] + list(GD)
    bad = [(i, k) for i, (g, r) in enumerate(zip(got, rows)) for k in keys if g[k] != r[k]]
    assert not bad, f"{len(bad)} stored final labels differ from the replay, first: {bad[:3]}"
    # the replay must exercise all three outcomes, otherwise it could not detect a broken branch
    assert any(r["needs_arbiter"] for r in rows) and any(not r["needs_arbiter"] for r in rows)
    assert any(r["general_disagree"] for r in rows)


# ---------------------------------------------------------------------------------------- builder golden
def _rebuild(name):
    stored = {r["request_key"]: r for r in runio.read_jsonl(ROOT / "runs" / "requests" / f"{name}.jsonl")}
    fams = []
    for f in sorted({r["items_file"] for r in stored.values()}):
        for line in (REQUEST_FILES[name] / f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                fam = json.loads(line)
                fam["_file"] = f
                if fam.get("dropped") is not True:
                    fams.append(fam)
    want = {r["family_id"] for r in stored.values()}
    fams = [f for f in fams if f["family_id"] in want]
    models = sorted({r["model"] for r in stored.values()})
    prompts = sorted({r["prompt_id"] for r in stored.values()})
    nss = sorted({r.get("namespace") for r in stored.values()}, key=lambda x: (x is not None, x or ""))
    chans = {t["channel"] for r in stored.values() for t in r["targets"]}
    built = {r["request_key"]: r for r in B.build(fams, models, prompts, [c for c in B.CHANNELS if c in chans], nss)}
    return stored, built


@pytest.mark.parametrize("name", sorted(REQUEST_FILES))
def test_builder_reproduces_stored_requests(name):
    stored, built = _rebuild(name)
    assert len(stored) > 1000
    assert set(built) == set(stored), f"{len(set(built) ^ set(stored))} request keys differ"
    for k, r in stored.items():
        b = built[k]
        assert b["input_text"] == r["input_text"], k
        assert b["prompt"] == r["prompt"], k
        assert sorted(json.dumps(t, sort_keys=True) for t in b["targets"]) == sorted(json.dumps(t, sort_keys=True) for t in r["targets"]), k
        assert (b["model"], b["prompt_id"], b["sample_idx"], b["temperature"]) == (r["model"], r["prompt_id"], r["sample_idx"], r["temperature"]), k
    # every channel of the stored files is covered, so a channel-specific builder fault cannot hide
    assert {t["channel"] for r in stored.values() for t in r["targets"]} == set(B.CHANNELS)
