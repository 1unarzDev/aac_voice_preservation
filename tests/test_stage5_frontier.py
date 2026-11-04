"""Stage 5, Parts 22-25 (src/make_frontier_parts.py): coder counts, exclusions, balance, blind files, sheets, tool.

Exclusions are recomputed here from the raw files (not through the builder's own helpers).
pytest-style; also runnable directly.
"""
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import make_assignments as MA  # noqa: E402
import make_frontier_parts as MF  # noqa: E402

ANN, PKG = ROOT / "annotation", ROOT / "annotation_package"
S5 = PKG / "stage5"
IDS = [f"P{i:02d}" for i in range(1, 21)]
PLAN = json.loads((ANN / "assignments" / "stage5_frontier.json").read_text())
ASSIGN = list(csv.DictReader(open(ANN / "assignments" / "stage5_frontier_assignment.csv")))
BY = defaultdict(list)
for r in ASSIGN:
    BY[(r["part"], r["item_id"])].append(r["annotator"])
N_ITEMS = {"part22": 223, "part23": 120, "part24": 73, "part25": 258}
COUNT = {"part22": 2, "part23": 3, "part24": 2, "part25": 3}


def _rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def _jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


def _hw_people():
    """family -> writer + every checker (check_key.csv incl. tie-breakers), hw and hw2, straight from the raw files."""
    out = defaultdict(set)
    for sub in ("", "hw2"):
        d = ANN / "written" / sub if sub else ANN / "written"
        for j in _jl(d / "hw_candidates.jsonl"):
            out[j["family_id"]].add(j["writer_id"])
        for r in _rows(d / "check_key.csv"):
            out[r["family_id"]].add(r["writer_id"])
            out[r["family_id"]] |= {t.split("_")[0] for t in r["check_id"].split()}
    return out


def _elic_people():
    sets = defaultdict(set)
    for r in _rows(ANN / "elicitation_assignment.csv"):
        sets[r["set"]].add(r["annotator"])
    return {j["item_id"]: sets[j["set"]] for j in _jl(ANN / "elicitation_key.jsonl")}


def _file_items(a, part):
    p = S5 / f"{a}_{part}.json"
    return json.loads(p.read_text())["items"] if p.exists() else []


def test_item_sets_and_coder_counts():
    assert PLAN["n_items"] == N_ITEMS and PLAN["coders"] == COUNT
    for part, n in N_ITEMS.items():
        keys = [k for k in BY if k[0] == part]
        assert len(keys) == n, part
        for k in keys:
            assert len(BY[k]) == COUNT[part] == len(set(BY[k])), (k, BY[k])
    # item sets are the requests' own: the 36 speech-act cue-lost + all 37 control items, 108+12, 197+61, 223
    voc = _rows(ANN / "frontier_value_of_cue_key.csv")
    want = {r["id"] for r in voc if (r["stratum"].startswith("A") and r["dimension"] == "speech_act") or r["stratum"].startswith("B")}
    assert {k[1] for k in BY if k[0] == "part24"} == want and len(want) == 73
    wm = json.load(open(ANN / "frontier_whole_message_items.json"))["items"]
    assert Counter(i["type"] for i in wm) == {"O": 108, "V": 12}
    pc = json.load(open(ANN / "frontier_partner_context_r3_items.json"))
    assert Counter(i["part"] for i in pc) == {"A": 197, "B": 61}


def test_exclusions_from_raw_files():
    hw, el = _hw_people(), _elic_people()
    dp = {r["item_id"]: r for r in _rows(ANN / "frontier_default_profiles_key.csv")}
    for (part, iid), who in BY.items():
        if part == "part22":
            assert not set(who) & el[dp[iid]["item"]], (iid, who)
    voc = {r["id"]: r for r in _rows(ANN / "frontier_value_of_cue_key.csv")}
    for (part, iid), who in BY.items():
        if part == "part24":
            assert not set(who) & el[voc[iid]["item_id"]], (iid, who)
            assert voc[iid]["writer"] not in who
    wm = {r["id"]: r for r in _rows(ANN / "frontier_whole_message_key.csv")}
    pc = {r["id"]: r for r in _rows(ANN / "frontier_partner_context_r3_key.csv")}
    n_blocking = 0
    for (part, iid), who in BY.items():
        fam = wm[iid]["family_id"] if part == "part23" else pc[iid]["family_id"] if part == "part25" else None
        if fam is None:
            continue
        if fam.startswith("r2pol-"):
            continue                                   # r2pol-* families exclude no one
        assert fam in hw, fam
        assert not set(who) & hw[fam], (iid, fam, who)
        n_blocking += 1
    assert n_blocking > 200
    # r2pol-* are really unconstrained in the builder
    assert all(not u["blocked"] for u in MF.part25(MF.hw_blocks())[0] if pc[u["item_id"]]["family_id"].startswith("r2pol-"))


def test_whole_message_no_two_arms_of_one_input():
    key = {r["id"]: r for r in _rows(ANN / "frontier_whole_message_key.csv")}
    seen = defaultdict(Counter)
    for a in IDS:
        for it in _file_items(a, "part23"):
            k = key[it["item_id"]]
            if k["kind"] == "output":
                seen[a][(k["family_id"], k["variant"])] += 1
    assert seen and all(max(c.values()) == 1 for c in seen.values())
    assert sum(1 for a in IDS if _file_items(a, "part23")) >= 9      # nine different people are needed for one input (3 arms x 3 coders)


def test_balance_and_parts_per_person():
    tot = PLAN["total_minutes"]
    assert set(tot) == set(IDS) and max(tot.values()) - min(tot.values()) <= 2, tot
    assert 58 <= sum(tot.values()) / 20 <= 61
    for a in IDS:
        parts = PLAN["per_person"][a]
        assert 2 <= len(parts) <= 3, (a, parts)
        assert all(v["n_items"] >= MF.MIN_PART_ITEMS for v in parts.values())
    # exact seconds including the 2 practice items per part, plus the 18 min of Parts 20 and 21
    secs = [sum(v["seconds"] for v in PLAN["per_person"][a].values()) + 18 * 60 for a in IDS]
    assert max(secs) - min(secs) <= 150, (min(secs), max(secs))


def test_files_match_assignment_and_are_blind():
    for a in IDS:
        for part in N_ITEMS:
            mine = sorted(k[1] for k, w in BY.items() if k[0] == part and a in w)
            f = S5 / f"{a}_{part}.json"
            assert f.exists() == bool(mine), (a, part)
            if not mine:
                continue
            doc = json.loads(f.read_text())
            assert doc["tool"] == "rate_items_v1" and doc["check_id"] == part and doc["n_items"] == len(mine) == PLAN["per_person"][a][part]["n_items"]
            assert sorted(i["item_id"] for i in doc["items"]) == mine and len(doc["practice"]) == 2
            assert doc["for"] == MF.id_hash(a, part)
            assert all(set(i) == {"item_id", "blocks", "qs"} for i in doc["items"])
            # wording of the tool text (not the real messages, which may contain any word, e.g. "fish and chips")
            txt = json.dumps({k: v for k, v in doc.items() if k != "items"}) + json.dumps([i["blocks"] and [b["label"] for b in i["blocks"]] for i in doc["items"]])
            assert not re.search(r"stratum|detector|machine|\bmodel|checker|\bjudge|weight|gpt|qwen|llama|mistral|gemini|intended|propositional|"
                                 r"exposure|frontier|hypothes|policy|chip|\barm\b", txt, re.I), (a, part)
    # Parts 20 and 21 stay exactly as built: 12 and 20 items per person
    for a in IDS:
        assert len(json.loads((S5 / f"{a}_part20.json").read_text())["items"]) == 12
        assert len(json.loads((S5 / f"{a}_part21.json").read_text())["items"]) == 20
    assert not list((PKG / "stage4").glob("*_part2[2-5].json")), "Stage 5 files must not be in stage4/"


def test_fresh_build_equals_committed():
    plan, al, built = MF.build(["part22", "part23", "part24", "part25"], ["part20", "part21"], write=False)
    assert plan == PLAN
    assert {(p, u["item_id"]): sorted(al.who[(p, u["item_id"])]) for p in built for u in built[p][0]} == {k: sorted(v) for k, v in BY.items()}


def test_assignment_csv_and_sheets_use_plain_names():
    rows = list(csv.DictReader(open(ANN / "assignments" / "stage5.csv")))
    per = Counter(r["task"] for r in rows)
    assert per["part20"] == per["part21"] == 20 and per["part25"] == 20 and per["part22"] == 11 and per["part24"] == 9
    for a in IDS:
        txt = (PKG / "assignments" / f"{a}_stage5.md").read_text()
        assert not re.search(r"frontier|stratum|detector|hypothes|propositional|echo|exposure|arm\b|chip|default profile|value of cue|whole message|partner context",
                             txt, re.I), a
    h = (PKG / "HANDOUT.md").read_text()
    s5 = h.split("<!-- stage5:start -->")[1].split("<!-- stage5:end -->")[0]
    assert not re.search(r"frontier|stratum|detector|hypothes|propositional|echo|exposure|chip", s5, re.I)
    assert "Wed Nov 4" in s5 and "Thu Nov 5, 23:59" in s5


def test_stage5_order_and_tool_static():
    html = (PKG / "rate_items.html").read_text()
    for needle in ("rate_items_v1", "labels_", "Download CSV", "localStorage", "ALLOWED_ITEM", "validateData"):
        assert needle in html
    assert not re.search(r"https?://", html), "tool must be self-contained"
    assert not (PKG / "item_check.html").exists()


def test_jsdom_every_part_file():
    node = shutil.which("node")
    mods = Path("/tmp/jsd/node_modules")
    if not node or not (mods / "jsdom").exists():
        return                                            # jsdom not installed here: the other tests still run
    seen = set()
    for f in sorted(S5.glob("P*_part2[2-5].json")):
        part = f.stem.split("_")[1]
        a = f.stem.split("_")[0]
        if part in seen and a not in ("P01", "P04", "P09"):   # all four parts for a few people, spot checks stay quick in pytest
            continue
        seen.add(part)
        r = subprocess.run([node, str(ROOT / "tests" / "test_rate_items_html.js"), str(PKG / "rate_items.html"), str(f), a],
                           capture_output=True, text=True, env={"NODE_PATH": str(mods), "PATH": "/usr/bin:/bin:/usr/local/bin"})
        assert r.returncode == 0 and "all ok" in r.stdout, (f.name, r.stdout[-600:], r.stderr[-600:])


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
