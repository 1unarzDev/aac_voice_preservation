"""Stage 1 assignment plan (src/make_assignments.py): constraints, outputs and sheets.

pytest-style (tmp_path); also runnable directly: python tests/test_assignments.py
Reads the committed elicitation session files; writes only into a temporary directory.
"""
import copy
import csv
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import make_assignments as MA  # noqa: E402

IDS = MA.parse_ids("P01..P20")


def _run(tmp: Path):
    return MA.run_stage1(IDS, out_assign=tmp / "assign", out_sheets=tmp / "sheets", out_stage2=tmp / "stage2",
                         written=tmp / "written", elic_assign=tmp / "elic.csv", pkg=tmp, quiet=True)


def test_parse_ids():
    assert IDS == [f"P{i:02d}" for i in range(1, 21)]
    assert MA.parse_ids("P01,P03") == ["P01", "P03"]


def test_stage1_constraints(tmp_path=None):
    tmp = Path(tmp_path or tempfile.mkdtemp())
    res = _run(tmp)
    plan, summ = res["plan"], res["summary"]
    # Part 9: every session once, 3 per set, 2-3 per person, no set twice
    files = [f for a in IDS for f in plan["elicitation"][a]]
    assert len(files) == len(set(files)) == 48
    assert set(summ["elic_sessions_per_set"].values()) == {3}
    for a in IDS:
        sets = [MA.elic_set(f) for f in plan["elicitation"][a]]
        assert 2 <= len(sets) <= 3 and len(sets) == len(set(sets))
    # audits: required counts reached, heavy coders do nothing else
    for t, need in MA.REQUIRED.items():
        assert summ["coverage"][t]["n"] >= need, t
    assert summ["coverage"]["part10"]["n"] == 3 and summ["coverage"]["parts13"]["n"] == 3
    # writing: 2 distinct dims each, 6-7 writers per dimension, 600 pairs
    assert sorted(summ["writers_per_dimension"].values()) == [6, 6, 7, 7, 7, 7]
    assert sum(summ["pairs_per_dimension"].values()) == 600
    # order: elicitation first, writing last, for everyone
    rows = list(csv.DictReader(open(tmp / "assign" / "stage1.csv")))
    for a in IDS:
        seq = [r["task"] for r in rows if r["annotator"] == a]
        n_e = len(plan["elicitation"][a])
        assert seq[:n_e] == ["elic"] * n_e and "elic" not in seq[n_e:]
        assert seq[-2:] == ["write", "write"] and seq.count("write") == 2
    # load balance
    lo, hi = summ["stage1_minutes_min_max"]
    assert 150 <= lo and hi <= 240 and hi - lo <= 60
    lo, hi = summ["audit_minutes_min_max_nonheavy"]
    assert lo >= 40 and hi <= MA.AUDIT_CAP
    # sheets + hand-out + writer sheet
    for a in IDS:
        s = (tmp / "sheets" / f"{a}.md").read_text()
        assert f"# Task sheet for {a}" in s and "No AI tools" in s
        for f in plan["elicitation"][a]:
            assert f"elicitation_sets/{f}.json" in s and f"keyword_elicitation_{f}_{a}.csv" in s
        for w in plan["writing"][a]:
            assert w["fragment"] in s and f"write_pairs_{w['dimension']}_{a}.csv" in s
        assert s.index("Part 9") < s.index("Part 7")
    assert "Stage 1" in (tmp / "HANDOUT.md").read_text()
    wa = list(csv.DictReader(open(tmp / "written" / "writer_assignment.csv")))
    assert len(wa) == 40 and Counter(r["writer_id"] for r in wa) == Counter({a: 2 for a in IDS})
    ea = list(csv.DictReader(open(tmp / "elic.csv")))
    assert len(ea) == 48 and {r["annotator"] for r in ea} == set(IDS)


def test_deterministic(tmp_path=None):
    a = MA.build_plan(IDS)
    b = MA.build_plan(IDS)
    assert a["elicitation"] == b["elicitation"] and a["audits"] == b["audits"] and a["writing"] == b["writing"]


def test_check_plan_catches_duplicate_set():
    plan = MA.build_plan(IDS)
    bad = copy.deepcopy(plan)
    a, b = IDS[0], IDS[1]
    # give a two replicates of one set by swapping a session with b
    sa = {MA.elic_set(f) for f in bad["elicitation"][a]}
    fb = next(f for f in bad["elicitation"][b] if MA.elic_set(f) in sa) if any(
        MA.elic_set(f) in sa for f in bad["elicitation"][b]) else None
    if fb is None:   # construct one directly
        s0 = MA.elic_set(bad["elicitation"][a][0])
        fb = next(f for f in bad["elic_sessions"] if MA.elic_set(f) == s0 and f not in bad["elicitation"][a])
        owner = next(x for x in IDS if fb in bad["elicitation"][x])
        b = owner
    i = bad["elicitation"][b].index(fb)
    j = next(k for k, f in enumerate(bad["elicitation"][a]) if MA.elic_set(f) != MA.elic_set(fb))
    bad["elicitation"][a][j], bad["elicitation"][b][i] = fb, bad["elicitation"][a][j]
    try:
        MA.check_plan(bad, MA.rows_for(bad))
    except SystemExit as e:
        assert "two replicates" in str(e)
    else:
        raise AssertionError("duplicate set not caught")


if __name__ == "__main__":
    test_parse_ids(); test_stage1_constraints(); test_deterministic(); test_check_plan_catches_duplicate_set()
    print("ALL PASSED")
