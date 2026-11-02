"""Stage 4 (D-058): roster rules, Part 16 check fill, hw2 dedup, and that hw1 data/plan are untouched.

pytest-style; also runnable directly: python tests/test_stage4.py
Writes only into temporary directories (the real stage4 files are not touched).
"""
import csv
import hashlib
import json
import re
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


# ---------------------------------------------------------------- Part 19 and the Part 17 comparison arms (2026-11-01)
import make_arbiter_check as MC  # noqa: E402
import runio  # noqa: E402

BASE120_SHA = "74b3415e4e78a6412ce9412c95ca194a71d3f28f0966e09437855b2315b9eafd"   # the original 120-row key (columns before the arms)


def test_part19_in_every_sheet_after_part18_and_part17_minutes(tmp_path=None):
    tmp = Path(tmp_path or tempfile.mkdtemp())
    res = _build(tmp)
    rows, s4 = res["rows"], res["stage4"]
    for a in res["plan"]["annotators"]:
        mine = sorted((r for r in rows if r["annotator"] == a), key=lambda r: r["order"])
        assert [r["task"] for r in mine][:2] == ["intent", "part19"], (a, [r["task"] for r in mine])
        r19 = mine[1]
        assert r19["return_file"] == f"labels_part19_{a}.csv" and r19["return_folder"] == "annotation/returns_arbiter_check/"
        assert f"stage4/{a}_part19.json" in r19["file_or_link"]
        txt = (tmp / "sheets" / f"{a}_stage4.md").read_text()
        assert "Part 19" in txt and f"labels_part19_{a}.csv" in txt
        steps = txt.split("## Steps")[1]
        assert steps.index("**1. Part 18:") < steps.index("**2. Part 19:") < (steps.index("**3. Part 17:") if a in s4["raters"] else 10 ** 9)
    for a in s4["raters"]:
        r17 = next(r for r in rows if r["annotator"] == a and r["task"] == "repair2")
        assert r17["expected_minutes"] == 47 and "80 sentences" in r17["description"]
        assert sum(r["expected_minutes"] for r in rows if r["annotator"] == a) == 15 + 10 + 47
    h = (tmp / "HANDOUT.md").read_text()
    assert "Part 19" in h and "labels_part19_<ID>" in h and "Parts 18 and 19 only" in h


def _recompute_blocked(items):
    b = {}
    for f, it in items.items():
        if it.get("writer_id"):
            b.setdefault(f, set()).add(it["writer_id"])
    for r in csv.DictReader(open(ROOT / "annotation" / "written" / "check_key.csv")):
        for c in r["check_id"].split():
            b.setdefault(r["family_id"], set()).add(c.rsplit("_check_", 1)[0] if "_check_" in c else c.rsplit("_tiebreak", 1)[0])
    ek = {r["id"]: r["set"] for r in map(json.loads, open(ROOT / "annotation" / "elicitation_key.jsonl"))}
    sets = {}
    for r in csv.DictReader(open(ROOT / "annotation" / "elicitation_assignment.csv")):
        sets.setdefault(r["set"], set()).add(r["annotator"])
    for f in items:
        if f.startswith("elic-") and f[5:] in ek:
            b.setdefault(f, set()).update(sets[ek[f[5:]]])
    return b


def test_part19_key_exclusions_loads_and_blind_files():
    key = list(csv.DictReader(open(ROOT / "annotation" / "arbiter_check_key.csv")))
    items = runio.load_items()
    blocked = _recompute_blocked(items)
    assert len(key) == 130 and Counter(k["source"] for k in key) == {"arbiter": 100, "canyou": 30}
    assert len({k["item_id"] for k in key}) == 130
    plan = json.loads(PLAN.read_text())
    load = Counter()
    for k in key:
        cs = k["coders"].split("|")
        assert len(cs) == 2 and len(set(cs)) == 2 and set(cs) <= set(plan["annotators"])
        assert not set(cs) & blocked.get(k["family_id"], set()), (k["item_id"], cs, blocked.get(k["family_id"]))
        load.update(cs)
    assert set(load) == set(plan["annotators"]) and set(load.values()) == {13}, load
    assert set(k["run"] for k in key) == {"r2c1", "hw1", "elic1"} and Counter(k["run"] for k in key if k["source"] == "canyou") == {"r2c1": 15, "hw1": 15}
    # arbiter labels come from the arbiter file; J1 and J2 differ on every arbiter unit
    arb = {}
    for run in ("r2c1", "hw1", "elic1"):
        for x in runio.read_jsonl(ROOT / "runs" / run / "arbiter.jsonl"):
            arb[(run, x["text_id"], x["family_id"])] = x["critical"]
    for k in key:
        if k["source"] == "arbiter":
            assert arb[(k["run"], k["text_id"], k["family_id"])] == k["arbiter_label"]
            assert k["J1"] != k["J2"] and k["arbiter_label"] in k["critical_options"].split("|")
        else:
            assert k["arbiter_label"] == "" and re.search(r"\b(can|could) you\b", k["text"], re.I)
    # the oversampled precedents are there
    tags = Counter(k["precedent_tag"] for k in key if k["source"] == "arbiter")
    for t in ("no_time_word_unclear", "hope_hedged", "sure_emphatic", "may_permission_plain", "want_please_request", "wonder_hedged"):
        assert tags[t] >= 2, (t, tags)
    # per-person blind files: items == the key's items for that person; no run/label leakage; Can-you question has no example
    by_id = {k["item_id"]: k for k in key}
    for a in plan["annotators"]:
        doc = json.loads((ROOT / "annotation_package" / "stage4" / f"{a}_part19.json").read_text())
        assert doc["run"] == "part19" and len(doc["practice"]) == 5 and len(doc["items"]) == 13
        assert {i["item_id"] for i in doc["items"]} == {k["item_id"] for k in key if a in k["coders"].split("|")}
        for it in doc["items"]:
            assert sorted(it) == ["critical", "input_text", "item_id", "text"]
            k = by_id[it["item_id"]]
            if k["source"] == "canyou":
                assert "'Can you" not in it["critical"]["question"] and "'Can I" not in it["critical"]["question"]
        blob = json.dumps(doc["items"]) + json.dumps(doc["practice"])
        assert not re.search(r"r2c1|hw1|elic1|arbiter|J1|J2|gemma|llama|qwen|terra", blob)
        assert not any(re.search(r"can you|could you", p["text"], re.I) for p in doc["practice"])


def test_part19_assign_respects_blocks_and_balances():
    ids = [f"P{i:02d}" for i in range(1, 11)]
    units = [{"families": f"f{i}", "run": "r", "text_id": f"t{i}", "family_id": f"f{i}"} for i in range(20)]
    blocked = {f"f{i}": {ids[i % 10], ids[(i + 1) % 10], ids[(i + 2) % 10]} for i in range(20)}
    load = MC.assign(units, ids, blocked)
    assert set(load.values()) == {4}, load
    for u in units:
        assert len(set(u["coders"])) == 2 and not set(u["coders"]) & blocked[u["families"]]


def test_part17_comparison_arms_in_key_and_files():
    key = list(csv.DictReader(open(ROOT / "annotation" / "repair_audit_v2_key.csv")))
    assert len(key) == 160 and Counter(r["arm"] for r in key) == {"repaired": 60, "control": 60, "original_failed": 20, "strip_only": 20}
    base_cols = ["item_id", "arm", "pool", "assigned_model", "source_id", "output_ids", "families", "dimensions", "channels",
                 "channel_group", "hash_rank", "hash", "raters", "input_text", "text", "eligible_after_exclusion"]
    base = [r for r in key if r["arm"] in ("repaired", "control")]
    assert key[:120] == base, "the 120 base rows must stay first"
    assert hashlib.sha256(json.dumps([[r[c] for c in base_cols] for r in base]).encode()).hexdigest() == BASE120_SHA
    for arm in ("original_failed", "strip_only"):
        for pool in ("discovery", "transfer"):
            assert sum(r["arm"] == arm and r["pool"] == pool for r in key) == 10
    import explode
    ex = {explode.normalise(r["text"]) for f in ("repair_audit_key.csv", "repair_audit_transfer_key.csv")
          for r in csv.DictReader(open(ROOT / "annotation" / f))}
    norm = [explode.normalise(r["text"]) for r in key]
    assert len(set(norm)) == 160 and not set(norm) & ex
    assert len({r["item_id"] for r in key}) == 160 and all(r["item_id"].startswith("rv-") for r in key)
    rep = {(r["pool"], r["source_id"]): r for r in key if r["arm"] == "repaired"}
    for r in key:
        assert len(set(r["raters"].split("|"))) == 3 and set(r["raters"].split("|")) <= set(MA.PART17_RATERS)
        if r["arm"] == "original_failed":
            assert (r["pool"], r["paired_source_id"]) in rep and r["paired_item_id"] == rep[(r["pool"], r["paired_source_id"])]["item_id"]
        if r["arm"] == "strip_only" and r["paired_source_id"]:
            assert (r["pool"], r["paired_source_id"]) in rep
    assert sum(r["arm"] == "original_failed" and r["paired_source_id"] != "" for r in key) == 20
    assert sum(r["arm"] == "strip_only" and r["paired_source_id"] != "" for r in key) >= 8
    load = Counter(x for r in key for x in r["raters"].split("|"))
    assert set(load) == set(MA.PART17_RATERS) and max(load.values()) <= 85 and min(load.values()) >= 78, load
    for rid in MA.PART17_RATERS:
        txt = (ROOT / "annotation_package" / "stage4" / f"repair_audit_v2_{rid}.html").read_text()
        ids = set(re.findall(r'"item_id":\s*"(rv-[0-9a-f]{6})"', txt))
        assert ids == {r["item_id"] for r in key if rid in r["raters"].split("|")}, rid
        assert not re.search(r"original_failed|strip_only|paired_source", txt)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
