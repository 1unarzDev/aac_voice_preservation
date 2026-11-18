"""Problem #6 (cue_human): draw the frozen sample and build blind label units + private key. Rules: analysis/cue_human/PLAN.md section 3.
Subcommand `draw` (this file so far): seeded stratified draw of 120 pairs, distinct-text units, blind unit file, private key.
Run: python src/make_cue_human.py draw
Writes: analysis/cue_human/sample_pairs.csv (private), annotation/cue_human_key.csv (+.sha256, private),
        annotation/cue_human_units_blind.json (unit_id, text, question, options, rule only)."""
import sys, re, json, hashlib, csv
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import analyze as A, analyze_hw1 as H, judge as J, cue_human_power as C

OPTIONS = ["statement", "question", "request/command", "refusal", "acceptance", "offer/suggestion", "unclear/mixed"]

def norm(t): return re.sub(r"[\s]+", " ", str(t).lower()).strip().rstrip(".!?,;: ").strip()

def speech_rule():
    m = re.search(r"^\* speech_act - .*$", J.RULES_J2, re.M); assert m; return m.group(0)[2:]

def full_frame():
    items = {}
    for p in ["data/items/hw.jsonl", "data/items/hw2.jsonl"]: items.update(A.load_items(str(ROOT / p)))
    raw = pd.concat([pd.read_parquet(ROOT / f"runs/{r}/scored.parquet") for r in ("hw1", "hw2")], ignore_index=True)
    d, _ = H.build(items, raw)
    return d[d.prompt_id.eq("P0") & d.dimension.eq("speech_act") & d.channel.isin(["chip1", "noncrit"])]

def draw():
    pop = C.population(); alloc = C.allocate(pop)
    pop = pop.sort_values(["family_id", "variant", "model"]).reset_index(drop=True)
    rng = np.random.default_rng(C.SEED)
    S = C.draw(pop, alloc, rng)
    f = full_frame(); key = ["family_id", "variant", "model"]
    rows = []
    for _, r in S.iterrows():
        for ch in ("chip1", "noncrit"):
            o = f[(f.family_id == r.family_id) & (f.variant == r.variant) & (f.model == r.model) & (f.channel == ch)]
            assert len(o) == 1, (r.family_id, r.variant, r.model, ch, len(o))
            o = o.iloc[0]
            rows.append(dict(output_id=o.output_id, family_id=r.family_id, variant=r.variant, model=r.model, writer_id=r.writer_id,
                             channel=ch, stratum=r.stratum, pi=r.pi, text=o.text, tnorm=norm(o.text), variant_value=o.cv,
                             machine_label=o.crit, label_source=o.label_source, J1=o.critical_J1, J2=o.critical_J2,
                             critical_match=bool(o.critical_match)))
    O = pd.DataFrame(rows)
    # label unit = distinct normalised text; ids ordered by seeded shuffle so ids carry no order information
    texts = sorted(O.tnorm.unique()); perm = np.random.default_rng(C.SEED + 1).permutation(len(texts))
    uid = {t: f"cu{perm[i]+1:03d}" for i, t in enumerate(texts)}
    O["unit_id"] = O.tnorm.map(uid)
    (ROOT / "analysis/cue_human").mkdir(exist_ok=True)
    O.drop(columns=["tnorm"]).to_csv(ROOT / "analysis/cue_human/sample_pairs.csv", index=False)
    K = O.groupby("unit_id").agg(output_ids=("output_id", lambda x: " ".join(x)), family=("family_id", lambda x: " ".join(sorted(set(x)))),
        variant=("variant", lambda x: " ".join(x)), model=("model", lambda x: " ".join(x)), channel=("channel", lambda x: " ".join(x)),
        stratum=("stratum", lambda x: " ".join(x)), pi=("pi", lambda x: " ".join(f"{v:.6f}" for v in x)),
        machine_label=("machine_label", lambda x: " ".join(x)), J1=("J1", lambda x: " ".join(x)), J2=("J2", lambda x: " ".join(x)),
        arbiter=("label_source", lambda x: " ".join(x)), text=("text", "first"), n_outputs=("output_id", "size")).reset_index()
    kp = ROOT / "annotation/cue_human_key.csv"; K.to_csv(kp, index=False)
    (ROOT / "annotation/cue_human_key.sha256").write_text(hashlib.sha256(kp.read_bytes()).hexdigest() + "  cue_human_key.csv\n")
    units = [dict(unit_id=u, text=t) for u, t in K[["unit_id", "text"]].sort_values("unit_id").itertuples(index=False)]
    blind = dict(question=J.CRITICAL_Q["speech_act"], options=OPTIONS, rule=speech_rule(), units=units)
    (ROOT / "annotation/cue_human_units_blind.json").write_text(json.dumps(blind, indent=1, ensure_ascii=False))
    print(f"pairs {len(S)} outputs {len(O)} units {len(K)} (shared-text units {(K.n_outputs>1).sum()}) writers sampled {S.writer_id.nunique()}")
    print(S.groupby("model").size().to_string()); print(O.groupby(["model", "channel"]).size().unstack().to_string())
    print(S.groupby(["model", S.stratum.str[-2:]]).size().unstack(fill_value=0).to_string())
    print(O.drop_duplicates("unit_id").groupby("model").size().to_string())

if __name__ == "__main__":
    assert sys.argv[1:] == ["draw"]; draw()
