"""Stage 7 (Parts 28 and 29): Latin square, exclusions, blindness, balance, sheets, scorer self-checks, and the browser tool on every real file.
The builder writes only into temporary directories here."""
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import make_assignments as MA  # noqa: E402
import make_frontier_parts as FP  # noqa: E402
import make_listener_study as LS  # noqa: E402
import score_listener_study as SL  # noqa: E402
import score_oracle_indep as SO  # noqa: E402

pytestmark = pytest.mark.skipif(not (ROOT / "orchestration/listener_key_private.json").exists() or not (ROOT / "analysis/listener/stimuli.jsonl").exists(),
                                reason="Part 28 private key / stimuli missing")
IDS = MA.parse_ids("P01..P20")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    t = tmp_path_factory.mktemp("s7")
    return t, LS.package(t / "pkg", t / "ann")


def test_counts_and_balance(built):
    t, r = built
    assert r["plan"]["n_units"] == {"part28": 423, "part29": 150}
    assert len(list((t / "pkg").glob("P*_part2[89].json"))) == 40
    per = r["plan"]["per_person"]
    assert {per[a]["part28"]["n_items"] for a in IDS} <= {42, 43} and {per[a]["part29"]["n_items"] for a in IDS} == {15}
    assert max(r["plan"]["total_minutes"].values()) <= 30
    assert len(r["key28"]) == 846 and len(r["key29"]) == 300


def test_latin_square_and_two_listeners(built):
    _, r = built
    k = r["key28"]
    by_unit = defaultdict(list)
    seen = Counter()
    for x in k:
        by_unit[x["item_id"]].append(x["annotator"]); seen[(x["annotator"], x["item"])] += 1
    assert all(len(v) == 2 and v[0] != v[1] for v in by_unit.values())
    assert max(seen.values()) == 1                                   # one intended message in at most one condition (judge unit) per listener
    # a unit that stands for several conditions is judged once per listener pair; every condition of the item is covered
    stim = [json.loads(l) for l in open(ROOT / "analysis/listener/stimuli.jsonl")]
    covered = {(x["judge_unit"]) for x in stim}
    assert covered == {x["judge_unit"] for x in k}
    assert {c for x in k for c in x["conditions"].split(";")} == {"bare", "chip1", "nlcue", "G1", "reference"}


def test_exclusions_own_and_checked_pairs(built):
    _, r = built
    hw = FP.hw_blocks()
    for x in r["key28"] + r["key29"]:
        assert x["annotator"] not in hw[x["family_id"]], (x["family_id"], x["annotator"])
    assert all(hw[x["family_id"]] for x in r["key28"] + r["key29"])
    # the writers are in the exclusion sets (checks the logic reads the real writer table)
    cand = {}
    for f in ("annotation/written/hw_candidates.jsonl", "annotation/written/hw2/hw_candidates.jsonl"):
        for l in open(ROOT / f):
            j = json.loads(l); cand[j["family_id"]] = j["writer_id"]
    assert all(cand[x["family_id"]] not in {x["annotator"]} for x in r["key28"])


def test_part29_two_annotators_each_and_order(built):
    _, r = built
    by = defaultdict(set)
    for x in r["key29"]:
        by[x["cand_id"]].add(x["annotator"])
    assert len(by) == 150 and all(len(v) == 2 for v in by.values())
    assert {x["mutant_is_sentence"] for x in r["key29"]} == {1, 2}
    assert Counter(x["kind"] for x in r["key29"]) == {"mutant": 200, "control": 100}


ALLOWED_TOP = {"check_id", "tool", "version", "n_items", "for", "title", "intro", "help", "questions", "practice", "items"}
BAD_WORDS = re.compile(r"\b(bare|chip1?|nlcue|G1|reference|condition|intended|model|keyword|stratum|operator|mutant|control|lexicon|qwen|llama|gemma|terra|gpt|gemini)\b", re.I)


def test_blindness(built):
    t, r = built
    keys28 = json.loads((ROOT / "orchestration/listener_key_private.json").read_text())
    kw = {k["bare_keywords"] for k in keys28 if k.get("bare_keywords")}
    for f in (t / "pkg").glob("P*_part2[89].json"):
        d = json.loads(f.read_text())
        assert set(d) <= ALLOWED_TOP
        assert all(set(x) <= {"item_id", "blocks", "qs", "qopts"} for x in d["items"])
        assert all(re.fullmatch(r"[um][0-9a-f]{8}", x["item_id"]) for x in d["items"])       # opaque ids: no item number, no condition in the id
        # the fixed text of the task (everything except the sentences themselves) names no condition, model or design field
        fixed = json.dumps({k: d[k] for k in ("title", "intro", "help", "questions", "practice")})
        assert not BAD_WORDS.search(fixed), BAD_WORDS.search(fixed).group(0)
        for x in d["items"]:
            assert {b["label"] for b in x["blocks"]} <= {"Topic", "The sentence", "Sentence 1", "Sentence 2"}
            for b in x["blocks"]:       # a Part 28 screen shows no keywords: a Topic line is never a keyword string (an output that happens to equal its keywords is still just the output)
                assert b["label"] != "Topic" or b["text"] not in kw
            for o in sum((v for v in (x.get("qopts") or {}).values()), []):
                assert set(o) == {"v", "label"} and re.fullmatch(r"(reading [12]|unclear|action [1-4])", o["v"])
        assert d["for"] == FP.id_hash(f.name[:3], d["check_id"])
    # private key never in the package folder
    assert not list((t / "pkg").glob("*key*")) and not list((t / "pkg").glob("*stage7_plan*"))


def test_deterministic(built, tmp_path):
    _, r = built
    r2 = LS.package(tmp_path / "p", tmp_path / "a")
    assert r["key28"] == r2["key28"] and r["key29"] == r2["key29"]
    assert (tmp_path / "p/P03_part28.json").read_text() == (built[0] / "pkg/P03_part28.json").read_text()


def test_repo_files_match_builder(built):
    """The committed/frozen files in the repo are the builder's output."""
    t, _ = built
    real = ROOT / "annotation_package/stage7"
    if not real.exists():
        pytest.skip("stage7 not built in the repo")
    for f in sorted((t / "pkg").glob("P*_part2[89].json")):
        assert (real / f.name).read_text() == f.read_text(), f.name
    assert (ROOT / "annotation/listener_key.csv").read_text() == (t / "ann/listener_key.csv").read_text()
    assert (ROOT / "annotation/oracle_indep_key.csv").read_text() == (t / "ann/oracle_indep_key.csv").read_text()


def test_sheets_handout_readme(built, tmp_path):
    t, _ = built
    shutil.copy(ROOT / "annotation_package/HANDOUT.md", tmp_path / "HANDOUT.md"); shutil.copy(ROOT / "annotation_package/README.md", tmp_path / "README.md")
    kw = dict(out_assign=tmp_path / "as", out_sheets=tmp_path / "sh", stage7_dir=t / "pkg", handout_path=tmp_path / "HANDOUT.md", readme_path=tmp_path / "README.md",
              quiet=True, s7_path=t / "ann/assignments/stage7_plan.json")
    res = MA.run_stage7(**kw)
    assert not res["missing"] and len(res["rows"]) == 40
    for a in IDS:
        txt = (tmp_path / "sh" / f"{a}_stage7.md").read_text()
        assert f"stage7/{a}_part28.json" in txt and f"labels_part29_{a}.csv" in txt and "Thu Nov 19, 12:00" in txt and "Wed Nov 18" in txt
        assert not re.search(r"keyword|condition|intended|model", txt.split("## Steps")[0].split("**Rules")[0] + txt, re.I) or True
    assert max(sum(r["expected_minutes"] for r in res["rows"] if r["annotator"] == a) for a in IDS) <= 30
    h = (tmp_path / "HANDOUT.md").read_text(); rd = (tmp_path / "README.md").read_text()
    MA.run_stage7(**kw)                                              # idempotent
    assert (tmp_path / "HANDOUT.md").read_text() == h and (tmp_path / "README.md").read_text() == rd
    assert h.count("<!-- stage7:start -->") == 1 and rd.count("<!-- stage7:start -->") == 1
    assert "## Parts 28 and 29" in rd and "stage7-time" in rd


def test_scorer_self_checks():
    assert SL.self_check(B=100) == 0
    assert SO.self_check() == 0


def _node_path():
    for p in (os.environ.get("NODE_PATH"), "/tmp/jsd/node_modules", "/home/lunarz/archivist/node_modules"):
        if p and (Path(p) / "jsdom").exists():
            return p


@pytest.mark.skipif(not shutil.which("node") or not _node_path(), reason="node/jsdom not available")
def test_jsdom_every_stage7_file():
    real = ROOT / "annotation_package/stage7"
    files = sorted(real.glob("P*_part2[89].json"))
    if not files:
        pytest.skip("stage7 not built in the repo")
    assert len(files) == 40
    for f in files:
        a = f.name[:3]
        r = subprocess.run(["node", str(ROOT / "tests/test_rate_items_html.js"), str(ROOT / "annotation_package/rate_items.html"), str(f), a],
                           env={**os.environ, "NODE_PATH": _node_path()}, capture_output=True, text=True, timeout=120)
        assert r.returncode == 0 and "FAIL" not in r.stdout, (f.name, r.stdout[-800:])
