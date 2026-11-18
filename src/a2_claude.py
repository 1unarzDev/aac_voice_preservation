"""A2 Claude-as-oracle: blind labelling of original and mutant texts with the judge codebook (analysis/oracle_indep2/PLAN.md)."""
import json, random, subprocess, sys, csv, os
from pathlib import Path
sys.path.insert(0, "src")
import judge as J
from labels import DEFINITIONS
ROOT = Path.cwd(); OUT = ROOT / "analysis/oracle_indep2/claude_labels.jsonl"
key = {r["cand_id"]: r for r in csv.DictReader(open("annotation/oracle_indep_key.csv"))}
OPTS = {"speech_act": ["statement", "question", "request/command", "refusal", "acceptance", "offer/suggestion", "unclear/mixed"],
        "agent": ["speaker", "addressee", "we/joint", "third party", "unclear/mixed"],
        "certainty": ["plain assertion", "hedged/uncertain", "strongly certain/emphatic", "unclear/mixed"],
        "politeness": ["plain", "polite", "unclear/mixed"], "polarity": ["affirmative", "negated", "unclear/mixed"],
        "time_quantity": ["past", "now", "later", "unclear/mixed"]}
units = []
for l in open("analysis/oracle_indep/candidates.jsonl"):
    c = json.loads(l); d = key[c["id"]]["target_dimension"]
    for role in ("original", "mutant"):
        units.append({"uid": f"{c['id']}_{role[0]}", "text": c[role], "dimension": d})
random.Random(20261118).shuffle(units)
res = {}
if OUT.exists():
    for l in open(OUT): x = json.loads(l); res[x["uid"]] = x
def prompt(batch):
    items = [{"id": u["uid"], "sentence": u["text"], "critical_question": J.critical_question(u["dimension"], OPTS[u["dimension"]]),
              "critical_options": OPTS[u["dimension"]]} for u in batch]
    return ("You are a careful linguistic annotator. You extract what a short message explicitly expresses.\n\n" + J.RULES_J1 +
            "\n\nFor each item answer ONLY its critical question with one of its critical_options (ignore the general-dimension instructions above; only 'critical' is wanted)."
            " Reply with ONLY a JSON array of objects {\"id\":..., \"critical\":...}, no prose.\n\nItems:\n" + json.dumps(items, ensure_ascii=False, indent=0))
def ask(batch):
    r = subprocess.run(["claude", "-p", "--model", "sonnet", "--tools", "", "--no-session-persistence", prompt(batch)], capture_output=True, text=True, cwd="/tmp", timeout=900)
    t = r.stdout; i, j = t.find("["), t.rfind("]")
    try:
        return {x["id"]: x["critical"] for x in json.loads(t[i:j + 1])}
    except Exception:
        return {}
todo = [u for u in units if u["uid"] not in res]
B = 40
for s in range(0, len(todo), B):
    batch = todo[s:s + B]; got = ask(batch)
    miss = [u for u in batch if got.get(u["uid"]) not in OPTS[u["dimension"]]]
    if miss:
        got2 = ask(miss)
        for u in miss:
            if got2.get(u["uid"]) in OPTS[u["dimension"]]: got[u["uid"]] = got2[u["uid"]]
    with open(OUT, "a") as fh:
        for u in batch:
            lab = got.get(u["uid"]); ok = lab in OPTS[u["dimension"]]
            fh.write(json.dumps({"uid": u["uid"], "dimension": u["dimension"], "label": lab if ok else "unclear/mixed", "fallback": not ok}) + "\n")
    print(s, len(miss), flush=True)
