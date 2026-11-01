"""Scorers for Parts 5-6 on synthetic returns built from the private keys (no human data)."""
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path, head, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(head); w.writerows(rows)


def run(script, csvs, out):
    subprocess.run([sys.executable, str(ROOT / "src" / script), *map(str, csvs), "--out", str(out)],
                   check=True, capture_output=True, text=True)
    return json.loads((out / "summary.json").read_text())


def test_wc_scorer_oracle(tmp_path):
    key = list(csv.DictReader(open(ROOT / "annotation/wc_source_check_key.csv", encoding="utf-8")))
    assert len(key) == 20 and not {"r2act-078", "r2act-079"} & {k["family_id"] for k in key}
    head = ["item_id", "annotator", "practice", "order", "dimension", "value_A", "value_B", "bare_fits", "differ_only",
            "unsure", "note", "time_ms", "started_at", "tool", "exported_at"]
    for a in ("O1", "O2"):
        rows = [["prac-1", a, 1, 1, "polarity", "negated", "affirmative", "yes", "yes", "", "", 1, "", "t", ""]]
        rows += [[k["item_id"], a, 0, i, k["dimension"], k["authored_A"], k["authored_B"], "yes", "yes", "", "", 30000, "", "t", ""]
                 for i, k in enumerate(key)]
        write(tmp_path / f"{a}.csv", head, rows)
    # third annotator: one invalid value, one unsure answer
    bad = [[k["item_id"], "O3", 0, i, k["dimension"], "bogus" if i == 0 else k["authored_A"], k["authored_B"],
            "yes", "yes", "bare" if i == 1 else "", "", 1, "", "t", ""] for i, k in enumerate(key)]
    write(tmp_path / "O3.csv", head, bad)
    S = run("score_wc_source_check.py", [tmp_path / f"{a}.csv" for a in ("O1", "O2", "O3")], tmp_path / "out")
    assert S["consensus"]["family_passes"]["k"] == 20 and S["consensus"]["family_passes"]["n"] == 20
    assert S["consensus"]["authored_match"]["n"] == 40
    assert S["per_annotator"]["O3"]["authored_match"]["unknown"] == 1
    assert S["per_annotator"]["O3"]["ambiguity_confirmed"]["unknown"] == 1
    assert any("bogus" in p for p in S["problems"])


def test_wb_scorer_oracle(tmp_path):
    key = list(csv.DictReader(open(ROOT / "annotation/wb_check_key.csv", encoding="utf-8")))
    assert len(key) == 100
    head = ["item_id", "annotator", "practice", "dimension", "p1_order", "p1_plausible", "p1_unsure", "p1_note", "p1_time_ms",
            "p2_order", "p2_value", "p2_unsure", "p2_note", "p2_time_ms", "p1_started_at", "p2_started_at", "tool", "exported_at"]
    rows = [[k["item_id"], "C1", 0, k["dimension"], 1, k["values_1"], 0, "", 1000, 1, k["src_1"], 0, "", 1000, "", "", "t", ""]
            for k in key]
    write(tmp_path / "C1.csv", head, rows)
    S = run("score_wb_check.py", [tmp_path / "C1.csv"], tmp_path / "out")
    c = S["consensus"]
    n_amb = sum(k["status"] == "confirmed_ambiguous" for k in key)
    assert c["amb_confirm_primary"] == {**c["amb_confirm_primary"], "k": n_amb, "n": n_amb, "unknown": 0}
    assert c["source_match_coder1"]["k"] == 100
    assert c["source_admissible_blind"]["k"] == sum(k["src_1"] in k["values_1"].split("|") for k in key)
    assert S["per_annotator"]["C1"]["ambiguity_vs_c1_amb"]["agree"] == 1.0


if __name__ == "__main__":   # runnable without pytest
    import tempfile
    for t in (test_wc_scorer_oracle, test_wb_scorer_oracle):
        with tempfile.TemporaryDirectory() as d:
            t(Path(d)); print("ok", t.__name__)
