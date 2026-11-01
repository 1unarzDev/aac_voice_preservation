"""B1 (human-written pairs) and B2 (keyword elicitation): rules, collector, batches, scorers, sets.

pytest-style (tmp_path); also runnable directly:  python tests/test_hw_elic.py   [--regen-fixture]
No model, judge or network calls. The B2 set test reads the committed elicitation files; the scorer
tests build synthetic returns. tests/fixtures/hw_rule_cases.json is the shared Python/JS parity
fixture (tests/test_write_pairs_html.js checks the page's port against it).
"""
import csv
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import hw_rules as H  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "hw_rule_cases.json"
WRITER_HEAD = ["row_type", "writer", "dimension", "pair_no", "situation", "topic", "topic_suggested", "sentence_A", "value_A",
               "sentence_B", "value_B", "keywords", "extra_word", "checks_ok", "problems", "warnings", "practice_answer",
               "practice_expected", "time_ms", "consent", "consent_at", "dim_source", "started_at", "tool", "exported_at"]
CHECK_HEAD = ["item_id", "annotator", "check_id", "practice", "order", "dimension", "value_A", "value_B", "bare_fits",
              "differ_only", "unsure", "note", "time_ms", "started_at", "tool", "exported_at"]
PAIRS = {
    "polarity": [("I want the window seat on the train.", "affirmative", "I don't want the window seat on the train.", "negated", "want window seat"),
                 ("The lift in our building is working.", "affirmative", "The lift in our building isn't working.", "negated", "lift working")],
    "speech_act": [("The pharmacy is open on Sunday.", "statement", "Is the pharmacy open on Sunday?", "question", "pharmacy open"),
                   ("Did you charge my phone overnight?", "question", "Charge my phone overnight.", "request/command", "charge phone")],
    "politeness": [("Please send me the photos from the wedding.", "polite", "Send me the photos from the wedding.", "plain", "send photos")],
    "certainty": [("The morning bus is probably late.", "hedged/uncertain", "The morning bus is late.", "plain assertion", "bus late")],
    "agent": [("I booked the dentist appointment for Friday.", "speaker", "You booked the dentist appointment for Friday.", "addressee", "book appointment")],
    "time": [("I finished the knitting project last month.", "past", "I'll finish the knitting project next month.", "later", "finish project")],
}
CASES = [
    ("polarity", {"A": "I want the window seat on the train.", "valA": "affirmative", "B": "I don't want the window seat on the train.", "valB": "negated", "keywords": "want window seat"}),
    ("polarity", {"A": "I’m not coming to the barbecue on Sunday.", "valA": "negated", "B": "I’m coming to the barbecue on Sunday.", "valB": "affirmative", "keywords": "not coming barbecue"}),
    ("polarity", {"A": "I want tea.", "valA": "affirmative", "B": "I want tea.", "valB": "affirmative", "keywords": "tea"}),
    ("polarity", {"A": "Dont feed the dog after six tonight.", "valA": "negated", "B": "Feed the dog after six tonight.", "valB": "affirmative", "keywords": "dont feed dog"}),
    ("speech_act", {"A": "You booked the taxi to the airport.", "valA": "statement", "B": "Can you book the taxi to the airport?", "valB": "request/command", "keywords": "book taxi"}),
    ("speech_act", {"A": "Where is the bus stop near here?", "valA": "question", "B": "The bus stop is near here.", "valB": "statement", "keywords": "where bus-stop ?"}),
    ("politeness", {"A": "Could you check the oven timer for me?", "valA": "polite", "B": "Can you check the oven timer for me?", "valB": "plain", "keywords": "check oven check"}),
    ("politeness", {"A": "Please water the plants on the balcony.", "valA": "polite", "B": "Water the plants on the balcony.", "valB": "plain", "keywords": "water plants", "situation": "x" * 150}),
    ("certainty", {"A": "Maybe the clinic is closed today.", "valA": "hedged/uncertain", "B": "The clinic is closed today.", "valB": "plain assertion", "keywords": "maybe clinic closed"}),
    ("certainty", {"A": "I think I left my keys at work.", "valA": "hedged/uncertain", "B": "I really left my keys at work.", "valB": "plain assertion", "keywords": "leave keys"}),
    ("agent", {"A": "She walks the dog every morning.", "valA": "third party", "B": "I walk the dog every morning.", "valB": "speaker", "keywords": "walks dog"}),
    ("agent", {"A": "My sister paid for the taxi home.", "valA": "third party", "B": "I paid for the taxi home.", "valB": "speaker", "keywords": "pay taxi"}),
    ("time", {"A": "I went to the gym near work.", "valA": "past", "B": "I'll go to the gym near work.", "valB": "later", "keywords": "went gym"}),
    ("time", {"A": "I'm watching the match on the big screen.", "valA": "now", "B": "I watched the match on the big screen.", "valB": "past", "keywords": "watch match"}),
    ("time", {"A": "I finished the knitting project for my niece in the small village last month.", "valA": "past", "B": "I'll finish it.", "valB": "later", "keywords": "finish project"}),
    ("polarity", {"A": "I booked the train tickets for Monday.", "valA": "affirmative", "B": "I didn't book the train tickets for Monday.", "valB": "negated", "keywords": "booked tickets"}),
]


def fixture_doc():
    out = []
    for dim, p in CASES:
        r = H.check_pair(p, dim)
        out.append({"dim": dim, "pair": p, "ok": r["ok"], "keywords": r["keywords"], "extra": r["extra"],
                    "problems": [m for _, m in r["problems"]], "warnings": [m for _, m in r["warnings"]]})
    return {"cases": out, "lists": {"CUES_ALL": sorted(H.CUES_ALL), "STOP": sorted(H.STOP),
                                    "NONCRIT_TIME_OK": sorted(H.NONCRIT_TIME_OK), "IRREG": H.IRREG}}


def py(script, *args):
    return subprocess.run([sys.executable, str(ROOT / "src" / script), *map(str, args)], check=True, capture_output=True, text=True)


def write_csv(path, head, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(head); w.writerows(rows)


# ------------------------------------------------------------------ B1 rules

def test_rules_match_fixture():
    assert FIXTURE.exists(), "run: python tests/test_hw_elic.py --regen-fixture"
    want = json.loads(FIXTURE.read_text())
    got = fixture_doc()
    assert got["lists"] == want["lists"]
    for g, w in zip(got["cases"], want["cases"]):
        assert g == w, (g["pair"], g, w)


def test_rules_key_cases():
    r = H.check_pair(CASES[0][1], "polarity")
    assert r["ok"] and r["extra"][0] == "train" and not r["warnings"]
    assert any("not" in m for _, m in H.check_pair(CASES[1][1], "polarity")["problems"])          # cue word
    r = H.check_pair(CASES[2][1], "polarity")
    assert {f for f, _ in r["problems"]} >= {"A", "B", "valB", "keywords"}                          # short, same, values, 1 kw
    assert any("dont" in m for _, m in H.check_pair(CASES[3][1], "polarity")["problems"])
    assert H.check_pair(CASES[4][1], "speech_act")["ok"]                                            # book/booked = base form
    msgs = " ".join(m for _, m in H.check_pair(CASES[5][1], "speech_act")["problems"])
    assert "where" in msgs and "letters and numbers" in msgs
    assert any("repeated" in m for _, m in H.check_pair(CASES[6][1], "politeness")["problems"])
    assert any(f == "situation" for f, _ in H.check_pair(CASES[7][1], "politeness")["problems"])
    assert any("booster" in m for _, m in H.check_pair(CASES[9][1], "certainty")["warnings"])
    assert any("walks" in m for _, m in H.check_pair(CASES[10][1], "agent")["problems"])            # agreement leak
    assert H.check_pair(CASES[11][1], "agent")["ok"]
    assert any("went" in m for _, m in H.check_pair(CASES[12][1], "time")["problems"])             # irregular past
    assert H.check_pair(CASES[13][1], "time")["ok"]
    assert any("13 words" in m or "words; use 4 to 12" in m for _, m in H.check_pair(CASES[14][1], "time")["problems"])
    r = H.check_pair(CASES[15][1], "polarity")
    assert r["ok"] and any("ending" in m for _, m in r["warnings"])                                   # non-strict dim: warning only


# ------------------------------------------------------------------ B1 pipeline

def writer_rows(w, dim, pairs, consent="yes", exported="2026-11-02T10:00:00Z"):
    rows = [["practice", w, dim, f"prac-{dim}-1", "", "", "", "a", "x", "b", "y", "k", "", "", "", "", 1, 1, 50, consent, "t", "hash", "s", "write_pairs_v1", exported]]
    for i, (a, va, b, vb, k) in enumerate(pairs, 1):
        rows.append(["pair", w, dim, i, "", "health", "health", a, va, b, vb, k, "", 1, "", "", "", "", 20000, consent,
                     "2026-11-02T10:00", "hash", "s", "write_pairs_v1", exported])
    return rows


def test_collect_check_score(tmp_path):
    ret = tmp_path / "ret"; ret.mkdir()
    ws = {}
    for i, (dim, pairs) in enumerate(PAIRS.items()):
        w = f"W{i + 1}"; ws[dim] = w
        write_csv(ret / f"write_pairs_{dim}_{w}.csv", WRITER_HEAD, writer_rows(w, dim, pairs))
    # an older export of W1 with different content is superseded by the later one
    write_csv(ret / "old_W1.csv", WRITER_HEAD, writer_rows("W1", "polarity", [PAIRS["polarity"][1]] * 2, exported="2026-11-01T00:00:00Z"))
    # no consent -> rejected; exact duplicate of W1's first pair by another writer -> rejected
    write_csv(ret / "nc.csv", WRITER_HEAD, writer_rows("W9", "polarity", [PAIRS["polarity"][0]], consent="no"))
    write_csv(ret / "dup.csv", WRITER_HEAD, writer_rows("W8", "polarity", [PAIRS["polarity"][0]]))
    out = tmp_path / "w"
    py("collect_written_pairs.py", *sorted(ret.glob("*.csv")), "--out-dir", out, "--checkers", "C1,C2,C3,W1",
       "--kept", tmp_path / "none.csv", "--target-per-dim", 10)
    cands = [json.loads(l) for l in (out / "hw_candidates.jsonl").open()]
    assert len(cands) == sum(len(p) for p in PAIRS.values())
    assert all(c["cluster_id"] == c["writer_id"] and c["split"] == "hw" for c in cands)
    assert {c["family_id"].split("-")[1] for c in cands} == {"pol", "act", "plt", "cer", "agt", "tim"}
    rej = list(csv.DictReader(open(out / "rejected.csv")))
    assert {r["writer"] for r in rej} == {"W8", "W9"}
    assert "consent" in next(r for r in rej if r["writer"] == "W9")["reasons"]
    assert "duplicate" in next(r for r in rej if r["writer"] == "W8")["reasons"]
    v = py("validate_items.py", out / "hw_candidates.jsonl")
    assert v.stdout.splitlines()[-1].startswith("0 errors")
    quota = (out / "quota_report.md").read_text()
    assert "| polarity |" in quota and "| time |" in quota
    # stable ids on re-run
    py("collect_written_pairs.py", *sorted(ret.glob("*.csv")), "--out-dir", out, "--kept", tmp_path / "none.csv", "--no-batches")
    assert [json.loads(l)["family_id"] for l in (out / "hw_candidates.jsonl").open()] == [c["family_id"] for c in cands]
    # blind check file
    files = sorted((out / "check_files").glob("*.json"))
    assert len(files) == 1
    doc = json.loads(files[0].read_text())
    blob = json.dumps(doc)
    assert all(set(it) == {"item_id", "dimension", "options", "context", "A", "B", "bare", "noncritical"} for it in doc["items"])
    assert not any(x in blob for x in ("hw-pol", "writer", "critical_value", "W1", "W2"))
    asg = list(csv.DictReader(open(out / "check_assignment.csv")))
    assert len(asg) == 1 and {asg[0][f"checker_{i}"] for i in (1, 2, 3)} == {"C1", "C2", "C3"}   # W1 wrote pairs in it
    key = list(csv.DictReader(open(out / "check_key.csv")))
    by = {c["family_id"]: c for c in cands}
    ret2 = tmp_path / "chk"; ret2.mkdir()
    first_pol = next(k for k in key if k["family_id"].startswith("hw-pol"))
    first_act = next(k for k in key if k["family_id"].startswith("hw-act"))
    for c in ("C1", "C2", "C3", "W1"):
        rows = [["prac-1", c, doc["check_id"], 1, 1, "polarity", "negated", "affirmative", "yes", "yes", "", "", 1, "", "t", "x"]]
        for i, k in enumerate(key):
            f = by[k["family_id"]]
            va, vb = f["variants"]["A"]["critical_value"], f["variants"]["B"]["critical_value"]
            bare, only, uns = "yes", "yes", ""
            if k is first_pol and c in ("C1", "C2"):
                only = "no"                                # 2 of 3 say not minimal -> drop
            if k is first_act and c == "C3":
                va = "unclear/mixed"                       # 1 of 3 disagrees -> keep
            if k is first_act and c == "C2":
                uns = "bare"; bare = ""                    # unsure is not a pass -> 1 pass left -> drop
            rows.append([k["item_id"], c, doc["check_id"], 0, i, f["dimension"], va, vb, bare, only, uns, "", 1000, "", "t", "x"])
        write_csv(ret2 / f"check_{c}.csv", CHECK_HEAD, rows)
    items_out = tmp_path / "hw.jsonl"
    py("score_pair_checks.py", *sorted(ret2.glob("*.csv")), "--key", out / "check_key.csv", "--candidates",
       out / "hw_candidates.jsonl", "--out", tmp_path / "an", "--items-out", items_out)
    S = json.loads((tmp_path / "an" / "summary.json").read_text())
    assert S["dropped"]["own_pair"] == sum(1 for k in key if k["writer_id"] == "W1")
    assert S["decisions"] == {"keep": len(cands) - 2, "drop": 2}
    kept = [json.loads(l) for l in items_out.open()]
    assert first_pol["family_id"] not in {k["family_id"] for k in kept}
    assert first_act["family_id"] not in {k["family_id"] for k in kept}
    assert all("content_sha" not in k and k["human_check"]["n_pass"] >= 2 for k in kept)
    assert py("validate_items.py", items_out).stdout.splitlines()[-1].startswith("0 errors")
    # exclusion list: drop C3 entirely. Left: C1, C2 and W1 (W1 only on other writers' pairs). The polarity
    # pair (W1's own) has C1/C2 "not minimal" -> drop; the speech-act pair now has C1 + W1 passing -> keep.
    py("score_pair_checks.py", *sorted(ret2.glob("*.csv")), "--key", out / "check_key.csv", "--candidates",
       out / "hw_candidates.jsonl", "--out", tmp_path / "an2", "--exclude", "C3", "--no-write")
    S2 = json.loads((tmp_path / "an2" / "summary.json").read_text())
    assert S2["dropped"]["excluded"] == len(key) and S2["decisions"] == {"keep": len(cands) - 1, "drop": 1}


def test_batches_balanced(tmp_path):
    import make_check_batches as MB
    cands = []
    for w in range(12):
        for j in range(15):
            d = list(H.DIMS)[w % 6]
            cands.append({"family_id": f"hw-{H.DIMS[d]['code']}-{w * 15 + j + 1:03d}", "writer_id": f"P{w + 1:02d}",
                          "dimension": H.DIMS[d]["family_dim"], "critical_options": H.DIMS[d]["options"], "context": None,
                          "variants": {"A": {"source": f"a {w} {j}", "critical_value": H.DIMS[d]["values"][0]},
                                       "B": {"source": f"b {w} {j}", "critical_value": H.DIMS[d]["values"][1]}},
                          "bare": "x y", "noncritical": "z"})
    cp = tmp_path / "c.jsonl"
    cp.write_text("".join(json.dumps(c) + "\n" for c in cands))
    checkers = [f"P{i:02d}" for i in range(1, 13)] + [f"C{i}" for i in range(1, 7)]
    assert MB.main(["--candidates", str(cp), "--out-dir", str(tmp_path), "--checkers", ",".join(checkers)]) == 0
    st = json.loads((tmp_path / "check_batches.json").read_text())
    sizes = [len(b["items"]) for b in st["batches"].values()]
    assert sum(sizes) == 180 and max(sizes) <= 30 and len(sizes) == 6
    load = Counter()
    for cid, cs in st["assignment"].items():
        b = st["batches"][cid]
        assert len(cs) == 3 == len(set(cs)) and not set(cs) & set(b["writers"])
        for c in cs:
            load[c] += 1
    assert max(load.values()) - min(load.values()) <= 1
    for f in (tmp_path / "check_files").glob("*.json"):
        d = json.loads(f.read_text())
        assert sorted(d["exclude"]) == sorted(MB.id_hash(w) for w in st["batches"][d["check_id"]]["writers"])
    # incremental: new candidates go to new batches, old batches unchanged
    old = json.dumps(st["batches"], sort_keys=True)
    extra = [dict(cands[0], family_id=f"hw-pol-{900 + i}", writer_id="P99") for i in range(10)]
    cp.write_text("".join(json.dumps(c) + "\n" for c in cands + extra))
    MB.main(["--candidates", str(cp), "--out-dir", str(tmp_path), "--checkers", ",".join(checkers)])
    st2 = json.loads((tmp_path / "check_batches.json").read_text())
    assert json.dumps({k: st2["batches"][k] for k in st["batches"]}, sort_keys=True) == old and len(st2["batches"]) == 7
    assert len(st2["batches"]["hwc007"]["items"]) == 10 and st2["batches"]["hwc007"]["writers"] == ["P99"]
    assert MB.id_hash("p07") == MB.id_hash("P07") and len(MB.id_hash("P07")) == 8


def test_writer_links(tmp_path):
    out = tmp_path / "wa.csv"
    py("make_writer_links.py", "--n", 60, "--out", out)
    rows = list(csv.DictReader(open(out)))
    per = Counter(r["dimension"] for r in rows)
    assert len(rows) == 60 and set(per.values()) == {10} and set(per) == set(H.DIMS)
    for d in H.DIMS:
        rots = [int(r["rot"]) for r in rows if r["dimension"] == d]
        assert len(set(rots)) == 10
    assert all(r["link_fragment"] == f"#dim={r['dimension']}&rot={r['rot']}&n=15&id={r['writer_id']}" for r in rows)


# ------------------------------------------------------------------ B2

def test_elicitation_sets_committed():
    key = [json.loads(l) for l in (ROOT / "annotation/elicitation_key.jsonl").open()]
    assert len(key) == 300 and len({k["id"] for k in key}) == 300
    assert Counter(k["sample"] for k in key) == {"random": 150, "enriched": 150}
    assert all(0 < k["inclusion_prob"] <= 1 for k in key)
    wb = [json.loads(l) for l in (ROOT / "data/specs/wb_sample.jsonl").open()]
    wb_ids = {r["id"] for r in wb} | {d for r in wb for d in r.get("duplicate_ids") or []}
    seeds = {f"aactext-train-{json.loads(l)['seed_line']:05d}" for p in ("r2_c1", "r2_c2")
             for l in (ROOT / f"data/items/{p}.jsonl").open() if json.loads(l).get("seed_line")}
    assert not ({k["id"] for k in key} & (wb_ids | seeds))
    files = sorted((ROOT / "annotation_package/elicitation_sets").glob("elic_s*_r*.json"))
    assert len(files) == 24
    by_set = {}
    for f in files:
        d = json.loads(f.read_text())
        assert set(d) == {"set_file", "set", "order", "tool", "version", "n", "messages"}
        assert all(set(m) == {"item_id", "text"} for m in d["messages"])
        by_set.setdefault(d["set"], []).append([m["item_id"] for m in d["messages"]])
    kid = {k["item_id"]: k for k in key}
    for s, orders in by_set.items():
        assert len(orders) == 3 and len({frozenset(o) for o in orders}) == 1 and 37 <= len(orders[0]) <= 38
        assert len({tuple(o) for o in orders}) == 3
        n = len(orders[0])                  # Latin square on 3 blocks: replicates 2 and 3 are rotations of 1
        for o in orders[1:]:
            assert any(o == orders[0][c:] + orders[0][:c] for c in range(1, n))
        assert all(kid[x]["set"] == s and len(set(kid[x]["positions_by_replicate"])) == 3 for x in orders[0])
    asg = list(csv.DictReader(open(ROOT / "annotation/elicitation_assignment.csv")))
    assert len(asg) == 24 and len({(r["annotator"], r["set"]) for r in asg}) == 24


def test_score_elicitation(tmp_path):
    key = [json.loads(l) for l in (ROOT / "annotation/elicitation_key.jsonl").open()]
    sub = [k for k in key if k["set"] == "s01"]
    head = ["item_id", "annotator", "set_file", "practice", "order", "message", "keywords", "n_words", "skipped", "note",
            "time_ms", "n_edits", "started_at", "tool", "exported_at"]
    for a in ("T1", "T2", "T3"):
        rows = []
        for i, k in enumerate(sub):
            words = (k["pos_cap4"] + ["thing", "stuff"])[:4]
            if a == "T2" and k["present"]["polarity"]:
                words = ["not"] + words[:3]
            if a == "T3" and i == 0:
                rows.append([k["item_id"], a, "elic_s01_r3", 0, i, k["text"], "", 0, 1, "", 10, 0, "", "t", "x"]); continue
            if a == "T3" and i == 1:
                words = ["one", "two", "three", "four", "five"]             # invalid count -> excluded
            rows.append([k["item_id"], a, "elic_s01_r1", 0, i, k["text"], " ".join(words), len(words), 0, "", 1000, 2, "", "t", "x"])
        write_csv(tmp_path / f"{a}.csv", head, rows)
    req = tmp_path / "req.jsonl"
    py("score_elicitation.py", *sorted(tmp_path.glob("T*.csv")), "--out", tmp_path / "out", "--items-out", tmp_path / "elic.jsonl",
       "--requests", req)
    S = json.loads((tmp_path / "out" / "summary.json").read_text())
    assert S["status_counts"] == {"ok": 3 * len(sub) - 2, "skipped": 1, "invalid_word_count": 1}
    pol = S["by_dimension"]["polarity"]
    if pol["n_messages_with_cue"]:
        # T1/T3 copy POS-cap4 (negation lost as in POS-cap4), T2 adds 'not' -> about 1/3 fewer losses
        assert pol["lenient"]["diff_human_minus_pos"] < 0
    sp = S["by_dimension"]["agent"]["strict"]
    assert sp["pos_cap4"]["n"] == S["by_dimension"]["agent"]["official_pos_cap4_token_metric"]["n"]
    # string-based strict metric reproduces s1_cues' token-position metric on the POS-cap4 words
    for d in ("polarity", "speech_act", "certainty", "politeness", "agent", "time"):
        x = S["by_dimension"][d]
        if x["n_messages_with_cue"]:
            assert x["strict"]["pos_cap4"]["k"] == x["official_pos_cap4_token_metric"]["k"], d
    reqs = [json.loads(l) for l in req.open()]
    assert {r["model"] for r in reqs} == {"qwen2.5-7b", "llama3.1-8b", "gemma3-4b", "gpt-6.1-terra"}
    assert {r["prompt_id"] for r in reqs} == {"P0", "P2", "S3"}
    chans = {t["channel"] for r in reqs for t in r["targets"]}
    assert {"human_T1", "human_T2", "human_T3", "pos_cap4"} <= chans
    assert all(r["input_text"].startswith("Keywords: ") for r in reqs)
    fams = [json.loads(l) for l in (tmp_path / "elic.jsonl").open()]
    assert all(set(f["variants"]["A"]["chips"]) <= set(f["variants"]["A"]["all_chips"]) for f in fams)


def _run_all():
    if "--regen-fixture" in sys.argv:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(fixture_doc(), indent=1, ensure_ascii=False) + "\n")
        print("wrote", FIXTURE)
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                if fn.__code__.co_argcount:
                    with tempfile.TemporaryDirectory() as d:
                        fn(Path(d))
                else:
                    fn()
                print("ok  ", name)
            except Exception as e:  # noqa: BLE001
                fails += 1
                print("FAIL", name, type(e).__name__, e)
                if isinstance(e, subprocess.CalledProcessError):
                    print(e.stdout[-2000:], e.stderr[-2000:])
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    _run_all()
