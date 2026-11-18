"""A2 NLI oracle on all 150 independent-mutant candidates (analysis/oracle_indep2/PLAN.md). Run with tmp/a2/venv python."""
import json, csv, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
M = "microsoft/deberta-large-mnli"
tok = AutoTokenizer.from_pretrained(M); mod = AutoModelForSequenceClassification.from_pretrained(M).eval()
lab = {int(k): v.upper() for k, v in mod.config.id2label.items()}
rows = [json.loads(l) for l in open("analysis/oracle_indep/candidates.jsonl")]
def pred(p, h):
    x = tok(p, h, return_tensors="pt")
    with torch.no_grad():
        pr = mod(**x).logits.softmax(-1)[0]
    return lab[int(pr.argmax())], pr.tolist()
out = []
for r in rows:
    f, pf = pred(r["original"], r["mutant"]); b, pb = pred(r["mutant"], r["original"])
    out.append({"id": r["id"], "fwd": f, "bwd": b, "p_con_fwd": round(pf[[k for k, v in lab.items() if v == "CONTRADICTION"][0]], 4),
                "p_con_bwd": round(pb[[k for k, v in lab.items() if v == "CONTRADICTION"][0]], 4)})
w = csv.DictWriter(open("analysis/oracle_indep2/nli_raw.csv", "w", newline=""), fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(lab, len(out))
