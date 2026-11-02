"""Stage 4 (D-058): roster rules, Part 16 check fill, hw2 dedup, and that hw1 data/plan are untouched.

pytest-style; also runnable directly: python tests/test_stage4.py
Writes only into temporary directories (the real stage4 files are not touched).
"""
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import collect_written_pairs as CW  # noqa: E402
import make_assignments as MA  # noqa: E402

PLAN = ROOT / "annotation" / "assignments" / "plan.json"
WA = ROOT / "annotation" / "written" / "writer_assignment.csv"
HW1_FILES = [PLAN, WA, ROOT / "annotation" / "written" / "hw_candidates.jsonl", ROOT / "annotation" / "written" / "rejected.csv",
             ROOT / "annotation" / "written" / "check_key.csv", ROOT / "annotation" / "assignments" / "stage2.csv",
             ROOT / "annotation" / "assignments" / "stage3.csv"]


def digest(paths):
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.exists()}


def _build(tmp: Path, **kw):
    hand = tmp / "HANDOUT.md"
    shutil.copy(ROOT / "annotation_package" / "HANDOUT.md", hand)
    return MA.run_stage4(out_assign=tmp / "assign", out_sheets=tmp / "sheets", out_stage4=tmp / "stage4", written=tmp / "hw2",
                         pkg=tmp, quiet=True, handout_path=hand, **kw)


def _fake_cands(writers, n=15):
    out = []
    for w in writers:
        for i in range(1, n + 1):
            fid = f"hw2-act-{len(out) + 1:03d}"
            out.append({"family_id": fid, "writer_id": w, "dimension": "speech_act", "critical_options": ["statement", "question"],
                        "context": None, "variants": {"A": {"source": f"S{fid}.", "critical_value": "statement"},
                                                      "B": {"source": f"Q{fid}?", "critical_value": "question"}},
                        "bare": "kw", "noncritical": "x"})
    return out


def test_stage4_roster_rules(tmp_path=None):
    tmp = Path(tmp_path or tempfile.mkdtemp())
    before = digest(HW1_FILES)
    res = _build(tmp)
    s4, plan = res["stage4"], res["plan"]
    prior = {r["writer_id"] for r in csv.DictReader(open(WA)) if r["dimension"] == "speech_act"}
    used_rots = {int(r["rot"]) for r in csv.DictReader(open(WA)) if r["dimension"] == "speech_act"}
    assert len(s4["writers"]) == 4 and len(set(s4["writers"])) == 4
    assert not set(s4["writers"]) & prior, "Part 15 writers must never have written speech_act in Stage 1"
    assert "P06" not in s4["writers"]
    assert not {s4["writer_rot"][w] for w in s4["writers"]} & used_rots
    assert len({s4["writer_rot"][w] for w in s4["writers"]}) == 4
    assert s4["raters"] == MA.PART17_RATERS
    assert not set(s4["writers"]) & set(s4["raters"]), "free non-raters exist, so writers should avoid the Part 17 list"
    assert len(s4["checkers"]) == 6 and len(set(s4["checkers"])) == 6
    assert not set(s4["checkers"]) & (set(s4["writers"]) | set(s4["raters"]))
    rows = res["rows"]
    assert {r["annotator"] for r in rows} == set(plan["annotators"])
    first = {r["annotator"]: r for r in rows if r["order"] == 1}
    assert all(r["task"] == "intent" for r in first.values()), "everyone does Part 18 first"
    for r in rows:
        assert r["return_folder"].startswith("annotation/returns_") and r["return_file"].endswith(".csv")
    # sheets for all 20 with rules, order, minutes, return names
    for a in plan["annotators"]:
        txt = (tmp / "sheets" / f"{a}_stage4.md").read_text()
        for needle in ("Work **alone**", "No AI tools", "own", "(in this order)", " min", f"intent_check_{a}.csv"):
            assert needle in txt, (a, needle)
    for w in s4["writers"]:
        txt = (tmp / "sheets" / f"{w}_stage4.md").read_text()
        assert "do not copy" in txt.lower() and f"write_pairs_speech_act_{w}.csv" in txt
    # placeholders fixed now
    for c in s4["checkers"]:
        assert json.loads((tmp / "stage4" / f"{c}_check_hw2.json").read_text())["n_items"] == 0
    assert digest(HW1_FILES) == before, "hw1 plan/data must not change"


def test_plan_frozen_fields_match_rebuild():
    plan = json.loads(PLAN.read_text())
    fresh = MA.build_plan(plan["annotators"])
    for k in ("annotators", "elicitation", "audits", "writing", "check_graph", "part12_coders"):
        assert plan[k] == fresh[k], f"hw1 plan field {k} drifted"


def test_fill_checks_three_checkers_never_writer(tmp_path=None):
    tmp = Path(tmp_path or tempfile.mkdtemp())
    res = _build(tmp)
    s4 = res["stage4"]
    cands = _fake_cands(s4["writers"])
    cp = tmp / "hw2" / "hw_candidates.jsonl"
    cp.write_text("".join(json.dumps(c) + "\n" for c in cands))
    before = digest(HW1_FILES)
    summ = MA.run_stage4_fill(cand_path=cp, out_assign=tmp / "assign", out_sheets=tmp / "sheets", out_stage4=tmp / "stage4",
                              written=tmp / "hw2", pkg=tmp, handout_path=tmp / "HANDOUT.md", quiet=True)
    assert summ["pairs_by_n_checkers"] == {3: 60}
    assert set(summ["load_pairs"]) == set(s4["checkers"])
    assert set(summ["load_pairs"].values()) == {30}, summ["load_pairs"]
    key = list(csv.DictReader(open(tmp / "hw2" / "check_key.csv")))
    assert len(key) == 60
    for k in key:
        cs = [c.rsplit("_check_hw2", 1)[0] for c in k["check_id"].split()]
        assert len(cs) == 3 and len(set(cs)) == 3
        assert k["writer_id"] not in cs and not set(cs) & set(s4["writers"])
    for c in s4["checkers"]:
        doc = json.loads((tmp / "stage4" / f"{c}_check_hw2.json").read_text())
        assert doc["check_id"] == f"{c}_check_hw2" and doc["n_items"] == 30 == len(doc["items"])
    assert digest(HW1_FILES) == before


def test_fill_checks_absent_checker_replaced_by_reserve(tmp_path=None):
    tmp = Path(tmp_path or tempfile.mkdtemp())
    s4 = _build(tmp)["stage4"]
    cp = tmp / "hw2" / "hw_candidates.jsonl"
    cp.write_text("".join(json.dumps(c) + "\n" for c in _fake_cands(s4["writers"])))
    gone = s4["checkers"][0]
    summ = MA.run_stage4_fill(cand_path=cp, out_assign=tmp / "assign", out_sheets=tmp / "sheets", out_stage4=tmp / "stage4",
                              written=tmp / "hw2", pkg=tmp, absent=[gone], handout_path=tmp / "HANDOUT.md", quiet=True)
    assert gone not in summ["load_pairs"] and s4["check_reserve"][0] in summ["load_pairs"]
    assert not (tmp / "stage4" / f"{gone}_check_hw2.json").exists()
    assert "Part 16" not in (tmp / "sheets" / f"{gone}_stage4.md").read_text().split("## Steps")[1]


def test_dedup_against_all_prior_pairs_including_rejected():
    prior = CW.prior_pairs(ROOT / "annotation" / "written" / "hw2", "hw2")
    assert any(p["status"] == "rejected" for p in prior) and any(p["status"] == "accepted" for p in prior)
    acc = next(p for p in prior if p["status"] == "accepted")
    rej = next(p for p in prior if p["status"] == "rejected")
    # exact (either order)
    why, _ = CW.dedup_flags(acc["B"], acc["A"], prior)
    assert any(w.startswith("exact duplicate pair") for w in why)
    why, _ = CW.dedup_flags(rej["A"], rej["B"], prior)
    assert any("rejected" in w for w in why)
    # near duplicate: one extra word on each sentence of a prior pair -> Jaccard >= .75
    ta, tb = acc["A"].rstrip(".?!"), acc["B"].rstrip(".?!")
    if len(CW.H.toks(ta)) >= 4 and len(CW.H.toks(tb)) >= 4:
        why, _ = CW.dedup_flags(ta + " today.", tb + " today?", prior)
        assert any("Jaccard" in w or "exact" in w for w in why), why
    # clearly new pair is not flagged
    why, _ = CW.dedup_flags("Zebras knit quietly.", "Do zebras knit quietly?", prior)
    assert not why
    assert CW.jac({"a", "b", "c"}, {"a", "b", "c", "d"}) == 0.75


def test_collect_batch_hw2_ids_and_paths():
    tmp = Path(tempfile.mkdtemp())
    hdr = ["row_type", "writer", "dimension", "pair_no", "situation", "topic", "topic_suggested", "sentence_A", "value_A",
           "sentence_B", "value_B", "keywords", "extra_word", "checks_ok", "problems", "warnings", "consent"]
    acc = next(p for p in CW.prior_pairs(tmp, "hw2") if p["status"] == "accepted")
    rows = [["pair", "P05", "speech_act", 1, "", "money", "transport", "The ladders are ready on the quay.", "statement",
             "Are the ladders ready on the quay?", "question", "ladders ready", "quay", 1, "", "", "yes"],
            ["pair", "P05", "speech_act", 2, "", "money", "transport", acc["A"], "statement", acc["B"], "question", "x y", "z", 1, "", "", "yes"]]
    f = tmp / "write_pairs_speech_act_P05.csv"
    with open(f, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(hdr); w.writerows(rows)
    r = subprocess.run([sys.executable, str(ROOT / "src" / "collect_written_pairs.py"), "--batch", "hw2", "--no-batches",
                        "--out-dir", str(tmp / "out"), str(f)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    cands = [json.loads(l) for l in open(tmp / "out" / "hw_candidates.jsonl")]
    assert [c["family_id"] for c in cands] == ["hw2-act-001"], (cands, r.stdout)
    rej = list(csv.DictReader(open(tmp / "out" / "rejected.csv")))
    assert any("exact duplicate pair" in x["reasons"] for x in rej), (rej, r.stdout)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
