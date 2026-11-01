"""End-to-end Stage 2/3 preparation on SYNTHETIC Stage 1/2 returns (all in a temp dir; real returns untouched).

  python tests/test_stage23.py [--keep DIR]

Uses the frozen annotation/assignments/plan.json (read only). Steps: fake writer CSVs (one writer short, one writer
missing) -> collect_written_pairs.py --no-batches -> make_assignments Stage 2 fill (fixed paths, checker graph,
absent rule) -> fake check returns (splits + one unreturned file) -> score_pair_checks.py -> Stage 3 tie-break
routing; fake elicitation returns -> score_elicitation.py (P0,S3) -> fake elic1 run -> make_gold_elic.py; fake hw1
run -> make_gold_hw.py. No model or network calls.
"""
import csv
import hashlib
import json
import random
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import make_assignments as MA  # noqa: E402

PLAN = ROOT / "annotation" / "assignments" / "plan.json"
O = ["photos", "tickets", "keys", "letters", "books", "forms", "notes", "plates", "towels", "boxes", "bags", "cards"]
P = ["train", "table", "shelf", "desk", "bench", "porch", "counter", "sofa", "bed"]
T = {"polarity": ("I want the {o} on the {p}.", "affirmative", "I don't want the {o} on the {p}.", "negated", "want {o}"),
     "speech_act": ("The {o} are ready on the {p}.", "statement", "Are the {o} ready on the {p}?", "question", "{o} ready"),
     "politeness": ("Please put the {o} on the {p}.", "polite", "Put the {o} on the {p}.", "plain", "put {o}"),
     "certainty": ("The {o} are probably ready on the {p}.", "hedged/uncertain", "The {o} are ready on the {p}.", "plain assertion", "{o} ready"),
     "agent": ("I moved the {o} to the {p}.", "speaker", "You moved the {o} to the {p}.", "addressee", "move {o}"),
     "time": ("I cleaned the {o} on the {p} yesterday.", "past", "I will clean the {o} on the {p} tomorrow.", "later", "clean {o}")}
WRITER_HEAD = ["row_type", "writer", "dimension", "pair_no", "situation", "topic", "topic_suggested", "sentence_A", "value_A",
               "sentence_B", "value_B", "keywords", "extra_word", "checks_ok", "problems", "warnings", "practice_answer",
               "practice_expected", "time_ms", "consent", "consent_at", "dim_source", "started_at", "tool", "exported_at"]
CHECK_HEAD = ["item_id", "annotator", "check_id", "practice", "order", "dimension", "value_A", "value_B", "bare_fits",
              "differ_only", "unsure", "note", "time_ms", "started_at", "tool", "exported_at"]
ELIC_HEAD = ["item_id", "annotator", "set_file", "practice", "order", "message", "keywords", "n_words", "skipped", "note",
             "time_ms", "n_edits", "started_at", "tool", "exported_at"]
SHORT_WRITER, SHORT_N = None, 12          # set from the plan: a writer returning 12 of 15 pairs in session 1
JUDGED = ["critical", "polarity", "speech_act", "agent", "certainty", "politeness", "added_content"]


def py(script, *args):
    r = subprocess.run([sys.executable, str(ROOT / "src" / script), *map(str, args)], capture_output=True, text=True)
    assert r.returncode in (0, 2), (script, r.stdout[-2000:], r.stderr[-3000:])
    return r.stdout


def wcsv(path, head, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(head); w.writerows(rows)


def h(s):
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


def fake_writer_returns(plan, ret: Path, missing: str, short: str):
    used = defaultdict(int)
    for a in plan["annotators"]:
        if a == missing:
            continue
        for w in plan["writing"][a]:
            d = w["dimension"]
            n = SHORT_N if (a == short and w["session"] == 1) else 15
            rows = []
            for i in range(1, n + 1):
                k = used[d]; used[d] += 1
                o, p = O[k % len(O)], P[k // len(O)]
                A, va, B, vb, kw = T[d]
                rows.append(["pair", a, d, i, "", "health", "health", A.format(o=o, p=p), va, B.format(o=o, p=p), vb,
                             kw.format(o=o, p=p), "", 1, "", "", "", "", 20000, "yes", "2026-11-03T10:00", "hash", "s",
                             "write_pairs_v1", "2026-11-03T10:30:00Z"])
            wcsv(ret / f"write_pairs_{d}_{a}.csv", WRITER_HEAD, rows)


def fake_run(run_dir: Path, fams: list[dict], channels_of, models=("m1", "m2")):
    """scored.parquet + judgments.jsonl in the shape attribute.py/judge.py write (synthetic labels)."""
    import pandas as pd
    import build_requests as B
    from explode import normalise
    rows, judg = [], {}
    for f in fams:
        for v in f["variants"]:
            for ch in channels_of(f, v):
                inp = B.input_text(f, v, ch)
                for m in models:
                    text = f"{f['variants'][v]['source'].rstrip('.?')} okay {len(rows)}."
                    tid = hashlib.sha1(normalise(text).encode()).hexdigest()[:16]
                    rnd = random.Random(tid)
                    opts = f["critical_options"]
                    j1 = rnd.choice(opts[:2]); j2 = j1 if rnd.random() < .85 else opts[-1]
                    crit = j1 if j1 == j2 else rnd.choice(opts[:2])
                    rows.append({"output_id": f"o-{tid}-{f['family_id']}-{v}", "text_id": tid, "model": m, "prompt_id": "P0",
                                 "family_id": f["family_id"], "variant": v, "channel": ch, "input_text": inp, "text": text,
                                 "valid": True, "judged": True, "dimension": f["dimension"], "critical": crit,
                                 "critical_source": "agree" if j1 == j2 else "fallback_J1",
                                 "violation": rnd.random() < .2, "assumption": rnd.random() < .2,
                                 "any_stance_addition": rnd.random() < .1, "added_content": rnd.choice(["yes", "no"])})
                    j = {"text_id": tid, "family_id": f["family_id"], "input_text": inp, "text": text, "dimension": f["dimension"]}
                    for d in JUDGED:
                        j[f"J1_{d}"] = j1 if d == "critical" else "x"
                        j[f"J2_{d}"] = j2 if d == "critical" else "x"
                    for d in JUDGED[1:]:
                        j[d] = "x"
                        if d != "added_content":
                            j[f"L0_{d}"] = "x"
                    j["critical"] = crit
                    judg[(tid, f["family_id"], inp)] = j
    run_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(run_dir / "scored.parquet")
    with open(run_dir / "judgments.jsonl", "w") as fh:
        for j in judg.values():
            fh.write(json.dumps(j) + "\n")
    return len(rows)


def test_stage23_end_to_end(tmp=None):
    tmp = Path(tmp or tempfile.mkdtemp(prefix="stage23_"))
    plan = json.loads(PLAN.read_text())
    R = plan["ring"]
    missing = R[5]                                   # writer who returns nothing (and is absent for Stage 2)
    short = R[11]
    # ---- Stage 1 synthetic writer returns -> candidates
    ret = tmp / "returns_written"
    fake_writer_returns(plan, ret, missing, short)
    out_w = tmp / "written"
    py("collect_written_pairs.py", *sorted(ret.glob("*.csv")), "--out-dir", out_w, "--assignment",
       ROOT / "annotation/written/writer_assignment.csv", "--kept", tmp / "none.csv", "--no-batches")
    cands = [json.loads(l) for l in (out_w / "hw_candidates.jsonl").open()]
    assert len(cands) == 19 * 30 - (15 - SHORT_N), len(cands)
    # ---- Stage 2 fill at fixed paths
    st2, asg = tmp / "stage2", tmp / "assign"
    summ = MA.run_stage2(plan_path=PLAN, cand_path=out_w / "hw_candidates.jsonl", out_stage2=st2,
                         key_path=out_w / "check_key.csv", out_assign=asg, returns_glob=str(ret / "*.csv"))
    assert summ["missing_writers"] == [missing] and summ["absent"] == [missing]
    present = [a for a in plan["annotators"] if a != missing]
    names = {p.stem for p in st2.glob("*_check_*.json")}
    assert names == {f"{a}_check_{k}" for a in present for k in (1, 2, 3)}, sorted(names)[:5]
    assert summ["pairs_by_n_checkers"] == {3: len(cands)}, summ["pairs_by_n_checkers"]
    key = {r["family_id"]: r for r in csv.DictReader(open(out_w / "check_key.csv"))}
    for p in st2.glob("*_check_*.json"):
        doc = json.loads(p.read_text())
        who = doc["check_id"].rsplit("_check_", 1)[0]
        assert doc["n_items"] <= 30 and len(doc["items"]) == doc["n_items"]
        assert all(set(x) == {"item_id", "dimension", "options", "context", "A", "B", "bare", "noncritical"} for x in doc["items"])
        assert MA_id_hash(who) not in doc["exclude"]               # never the checker's own pairs
    loads = Counter(summ["load_pairs"].values())
    graph_checkers_of_missing = {e["checker"] for e in plan["check_graph"] if e["writer"] == missing}
    # freed checkers took over the absent person's chunks one-to-one: their load stays 90 (or less if short)
    assert all(summ["load_pairs"][c] <= 90 for c in summ["load_pairs"]) and max(summ["load_pairs"].values()) == 90
    reassigned = [l for l in summ["log"] if l.startswith(f"absent {missing}")]
    assert len(reassigned) == 18 and all("freed by" in l for l in reassigned), reassigned[:3]
    assert {l.split(" -> ")[1].split(" ")[0] for l in reassigned} == graph_checkers_of_missing
    # short writer: the session-1 chunk 2 shrank to 2 pairs, checkers unchanged
    sh = [c for c in cands if c["writer_id"] == short and c["writer_pair_no"] > 10
          and c["writer_dimension"] == plan["writing"][short][0]["dimension"]]
    assert len(sh) == SHORT_N - 10
    for c in sh:
        want = {e["checker"] for e in plan["check_graph"] if e["writer"] == short and e["chunk"] == 2}
        got = {x.rsplit("_check_", 1)[0] for x in key[c["family_id"]]["check_id"].split()}
        if missing in want:                         # the absent person's slot moved to a freed checker
            assert want - {missing} <= got and len(got) == 3 and missing not in got
        else:
            assert got == want
    # ---- synthetic Stage 2 check returns: some splits, one file never returned
    hwret = tmp / "returns_hwcheck"
    skip = f"{present[0]}_check_2"
    for p in sorted(st2.glob("*_check_*.json")):
        doc = json.loads(p.read_text())
        if doc["check_id"] == skip:
            continue
        who = doc["check_id"].rsplit("_check_", 1)[0]
        rows = []
        for i, it in enumerate(doc["items"]):
            k = next(v for v in key.values() if v["item_id"] == it["item_id"])
            fail = h(f"{who}|{it['item_id']}") % 6 == 0
            rows.append([it["item_id"], who, doc["check_id"], 0, i, it["dimension"], k["value_A"],
                         k["value_B"], "yes", "no" if fail else "yes", "", "", 5000, "s", "check_pairs_v1", "2026-11-06T10:00:00Z"])
        wcsv(hwret / f"check_pairs_{doc['check_id']}_{who}.csv", CHECK_HEAD, rows)
    hwchk = tmp / "hw_checks"
    py("score_pair_checks.py", *sorted(hwret.glob("*.csv")), "--key", out_w / "check_key.csv",
       "--candidates", out_w / "hw_candidates.jsonl", "--out", hwchk, "--items-out", tmp / "hw.jsonl")
    items = list(csv.DictReader(open(hwchk / "items.csv")))
    assert any(int(r["n_checks"]) < 3 for r in items) and any(r["n_pass"] == "2" and r["n_checks"] == "3" for r in items)
    # ---- Stage 3 routing
    st3 = tmp / "stage3"
    res = MA.run_stage3(plan_path=PLAN, items_path=hwchk / "items.csv", key_path=out_w / "check_key.csv",
                        cand_path=out_w / "hw_candidates.jsonl", out_stage3=st3, out_assign=asg)
    assert {p.stem for p in st3.glob("*_tiebreak.json")} == {f"{t}_tiebreak" for t in plan["tiebreakers"]}
    by_item = {r["family_id"]: r for r in items}
    planned = defaultdict(set)
    for fid, k in key.items():
        for c in k["check_id"].split():
            planned[fid].add(c.rsplit("_check_", 1)[0])
    for t, fids in res["routed"].items():
        assert len(fids) <= MA.TIEBREAK_CAP and len(fids) == len(set(fids))
        for fid in fids:
            r = by_item[fid]
            assert t != r["writer_id"] and t not in r["checkers"].split() and t not in planned[fid]
    n_routed = sum(len(v) for v in res["routed"].values())
    assert n_routed + len(res["overflow"]) >= res["n_need"][1] + res["n_need"][2]
    # ---- make_gold_hw on a synthetic hw1 run
    hw = [json.loads(l) for l in (tmp / "hw.jsonl").open()]
    assert len(hw) > 200
    run_hw = tmp / "runs" / "hw1"
    fake_run(run_hw, hw, lambda f, v: ["bare", "noncrit", "chip1", "chipall", "full"])
    gout = tmp / "stage3" / "part13_gold_hw.json"
    import make_gold_hw as MH
    MH.main(["--run-dir", str(run_hw), "--items", str(tmp / "hw.jsonl"), "--check-key", str(out_w / "check_key.csv"),
             "--part-out", str(gout), "--key-out", str(tmp / "gold_key_hw.csv"), "--sample-out", str(tmp / "gold_sample_hw.json")])
    part = json.loads(gout.read_text())
    assert 120 <= len(part["items"]) <= 180 and part["run"] == "gold_hw" and len(part["practice"]) == 5
    blob = json.dumps(part["items"])
    assert "hw-" not in blob and "m1" not in blob and "P0" not in blob
    gk = list(csv.DictReader(open(tmp / "gold_key_hw.csv")))
    fam_w = {f["family_id"]: f["writer_id"] for f in hw}
    coders = set(plan["part13_coders"])
    for r in gk:
        for f in r["families"].split("|"):
            assert fam_w[f] not in coders
            assert not (planned[f] & coders)
    # ---- elicitation: synthetic returns for all 48 sessions -> score -> elic1 run -> make_gold_elic
    ekey = [json.loads(l) for l in (ROOT / "annotation/elicitation_key.jsonl").open()]
    ea = list(csv.DictReader(open(ROOT / "annotation/elicitation_assignment.csv")))
    elret = tmp / "returns_elic"
    for s in ea:
        stem = Path(s["file"]).stem
        msgs = json.loads((ROOT / "annotation_package" / s["file"]).read_text())["messages"]
        a = s["annotator"]
        rows = []
        for i, m in enumerate(msgs):
            k = next(x for x in ekey if x["item_id"] == m["item_id"])
            words = (k["pos_cap4"] + ["thing", "stuff"])[:2 + h(a + m["item_id"]) % 3]
            rows.append([m["item_id"], a, stem, 0, i, m["text"], " ".join(words), len(words), 0, "", 1000, 1, "", "t", "x"])
        wcsv(elret / f"keyword_elicitation_{stem}_{a}.csv", ELIC_HEAD, rows)
    py("score_elicitation.py", *sorted(elret.glob("*.csv")), "--out", tmp / "elic_out", "--items-out", tmp / "elic.jsonl",
       "--requests", tmp / "elic_req.jsonl", "--prompts", "P0,S3")
    reqs = [json.loads(l) for l in (tmp / "elic_req.jsonl").open()]
    assert {r["prompt_id"] for r in reqs} == {"P0", "S3"}
    efams = [json.loads(l) for l in (tmp / "elic.jsonl").open()]
    assert len(efams) == 600
    run_el = tmp / "runs" / "elic1"
    fake_run(run_el, efams, lambda f, v: list(f["custom_channels"][v]))
    import make_gold_elic as ME
    eout = tmp / "stage2" / "part12_gold_elic.json"
    ME.main(["--run-dir", str(run_el), "--items", str(tmp / "elic.jsonl"), "--part-out", str(eout),
             "--key-out", str(tmp / "gold_key_elic.csv"), "--sample-out", str(tmp / "gold_sample_elic.json")])
    part = json.loads(eout.read_text())
    assert 120 <= len(part["items"]) <= 180 and part["run"] == "gold_elic"
    assert "elic-" not in json.dumps(part["items"]) and "human_" not in json.dumps(part["items"])
    eset = {k["id"]: k["set"] for k in ekey}
    for r in csv.DictReader(open(tmp / "gold_key_elic.csv")):
        for f in r["families"].split("|"):
            assert eset[f[len("elic-"):]] not in {"s01", "s02", "s03", "s04"}
        assert not any(c in r["channels"].split("|") for c in [f"human_{x}" for x in ("P03", "P08", "P13", "P19")])
        assert any(c.startswith("human_") for c in r["channels"].split("|"))
    design = json.loads((tmp / "gold_sample_elic.json").read_text())
    assert design["exclusions"]["excluded_set"] > 0
    print("tmp:", tmp)


def MA_id_hash(x):
    import make_check_batches as MB
    return MB.id_hash(x)


def test_frozen_plan_unchanged():
    """Stage 1 is in annotators' hands: rebuilding the plan must reproduce plan.json and every Stage 1 file."""
    plan = json.loads(PLAN.read_text())
    tmp = Path(tempfile.mkdtemp(prefix="stage1_"))
    MA.run_stage1(plan["annotators"], out_assign=tmp / "a", out_sheets=tmp / "s", out_stage2=tmp / "st2",
                  written=tmp / "w", elic_assign=tmp / "e.csv", pkg=tmp, quiet=True)
    # "dates" is display text only (Stage 2 was moved to Nov 1 after Stage 1 returned early, D-049); the plan itself is frozen
    nodates = lambda d: {k: v for k, v in d.items() if k != "dates"}  # noqa: E731
    assert nodates(json.loads((tmp / "a" / "plan.json").read_text())) == nodates(plan)
    for a in plan["annotators"]:
        assert (tmp / "s" / f"{a}.md").read_text() == (ROOT / "annotation_package/assignments" / f"{a}.md").read_text(), a
    assert (tmp / "a" / "stage1.csv").read_text() == (ROOT / "annotation/assignments/stage1.csv").read_text()
    assert (tmp / "e.csv").read_text() == (ROOT / "annotation/elicitation_assignment.csv").read_text()
    assert (tmp / "w" / "writer_assignment.csv").read_text() == (ROOT / "annotation/written/writer_assignment.csv").read_text()
    assert (tmp / "HANDOUT.md").read_text() == (ROOT / "annotation_package/HANDOUT.md").read_text()


if __name__ == "__main__":
    keep = sys.argv[sys.argv.index("--keep") + 1] if "--keep" in sys.argv else None
    test_frozen_plan_unchanged()
    test_stage23_end_to_end(keep)
    print("ALL PASSED")
