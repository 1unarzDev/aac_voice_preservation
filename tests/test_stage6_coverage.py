"""Stage 6 (Parts 26/27): builder invariants, blind files, sheets, scorer self-check, and the browser tool on the real files.
Writes only into temporary directories."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import make_assignments as MA  # noqa: E402
import make_coverage_stage6 as B6  # noqa: E402
import score_coverage as SC  # noqa: E402

pytestmark = pytest.mark.skipif(not (ROOT / "analysis/coverage/drafts_main.jsonl").exists(), reason="frozen coverage drafts missing")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    t = tmp_path_factory.mktemp("s6")
    r = B6.build(t / "pkg", t / "ann")
    return t, r


def test_design_counts(built):
    t, r = built
    s = r["summary"]
    assert all(v == 25 for v in s["cells"].values()) and len(s["cells"]) == 8
    assert len(list((t / "pkg/stage6").glob("P*_part2[67].json"))) == 40
    assert 24 <= s["minutes_min_max"][0] and s["minutes_min_max"][1] <= 30
    sv = [k for k in r["key"] if k["kind"] == "sv"]
    assert len(sv) == 200 and {k["annotator"] for k in sv} == set(MA.parse_ids("P01..P20"))
    for w in MA.parse_ids("P01..P20"):
        mine = [k for k in sv if k["annotator"] == w]
        assert sum(k["cond"] == "bare" for k in mine) == 5 and len(mine) == 10
        for cond in ("bare", "chip"):
            arms = [k["arm"] for k in mine if k["cond"] == cond]
            assert set(arms) == set(B6.ARMS)


def test_sets_equal_size_and_filtered(built):
    _, r = built
    sv = [k for k in r["key"] if k["kind"] == "sv"]
    full = [k for k in sv if int(k["k"]) == 3]
    assert sum(int(k["n_shown"]) == 3 for k in full) / len(full) >= 0.97
    assert all(int(k["n_shown"]) == 1 for k in sv if k["arm"] == "G1")
    for k in sv:
        texts = json.loads(k["set_texts"])
        assert len(texts) == len({x.lower() for x in texts})          # no duplicate drafts in a set


    t, _ = built
    for f in (t / "pkg/stage6").glob("P*_part2[67].json"):
        d = json.loads(f.read_text())
        w = f.name[:3]
        assert d["tool"] == "rate_items_v1" and d["for"] == B6.id_hash(w, d["check_id"])
        assert set(d) <= {"check_id", "tool", "version", "n_items", "for", "title", "intro", "help", "questions", "practice", "items"}
        assert all(set(x) == {"item_id", "blocks", "qs"} for x in d["items"])
        txt = f.read_text()
        assert '"arm' not in txt and '"cell' not in txt and "D3p" not in txt and "pool_arms" not in txt


def test_deterministic(built, tmp_path):
    _, r = built
    r2 = B6.build(tmp_path / "p", tmp_path / "a")
    assert [k["item_id"] for k in r["key"]] == [k["item_id"] for k in r2["key"]]
    assert [k.get("set_texts") for k in r["key"]] == [k.get("set_texts") for k in r2["key"]]


def test_sheets_and_handout(built, tmp_path):
    t, _ = built
    shutil.copy(ROOT / "annotation_package/HANDOUT.md", tmp_path / "HANDOUT.md")
    res = MA.run_stage6(out_assign=tmp_path / "as", out_sheets=tmp_path / "sh", stage6_dir=t / "pkg/stage6", handout_path=tmp_path / "HANDOUT.md",
                        quiet=True, s6_path=t / "ann/assignments/stage6_coverage.json")
    assert not res["missing"] and len(res["rows"]) == 40
    for a in MA.parse_ids("P01..P20"):
        s = (tmp_path / "sh" / f"{a}_stage6.md").read_text()
        assert f"stage6/{a}_part26.json" in s and f"labels_part27_{a}.csv" in s and "Part 26 first" in s
        assert "D3p" not in s and "arm" not in s.lower().replace("warm", "")
    h = (tmp_path / "HANDOUT.md").read_text()
    assert h.count("<!-- stage6:start -->") == 1
    MA.run_stage6(out_assign=tmp_path / "as", out_sheets=tmp_path / "sh", stage6_dir=t / "pkg/stage6", handout_path=tmp_path / "HANDOUT.md",
                  quiet=True, s6_path=t / "ann/assignments/stage6_coverage.json")
    assert (tmp_path / "HANDOUT.md").read_text() == h             # idempotent


def test_scorer_primitives():
    assert abs(SC.kappa([1, 0, 1, 0], [1, 0, 1, 0]) - 1) < 1e-9
    assert SC.holm({"a": 0.01, "b": 0.04, "c": 0.5}) == {"a": 0.03, "b": 0.08, "c": 0.5}
    assert SC.judge_status("gain", 0.12, 0.03, 0.2) == "pass" and SC.judge_status("gain", 0.02, -0.05, 0.08) == "fail"
    assert SC.judge_status("gain", 0.05, -0.02, 0.12) == "unresolved" and SC.judge_status("noninf", -0.01, -0.04, 0.03) == "pass"


@pytest.mark.skipif(not (ROOT / "annotation/coverage_key.csv").exists(), reason="Stage 6 key not built")
def test_self_check_passes():
    assert SC.self_check(B=100) == 0


def _node_path():
    for p in (os.environ.get("NODE_PATH"), "/tmp/jsd/node_modules", "/home/lunarz/archivist/node_modules"):
        if p and (Path(p) / "jsdom").exists():
            return p


@pytest.mark.skipif(not shutil.which("node") or not _node_path(), reason="node/jsdom not available")
def test_browser_tool_on_real_files(built):
    t, _ = built
    for part in ("part26", "part27"):
        for w in ("P01", "P09", "P20"):
            f = t / "pkg/stage6" / f"{w}_{part}.json"
            r = subprocess.run(["node", str(ROOT / "tests/test_rate_items_html.js"), str(ROOT / "annotation_package/rate_items.html"), str(f), w],
                               env={**os.environ, "NODE_PATH": _node_path()}, capture_output=True, text=True, timeout=120)
            assert r.returncode == 0 and "FAIL" not in r.stdout, r.stdout[-800:]
