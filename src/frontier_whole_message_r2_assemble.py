"""Assemble round-2 generations into (a) the judge run (runs/frontier_whole_message_r2/outputs.jsonl) and (b) M1 job lists.
  python src/frontier_whole_message_r2_assemble.py judgerun
  python src/frontier_whole_message_r2_assemble.py m1 [stage]     # runs gpt M1 jobs in declared priority order"""
import asyncio, hashlib, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import runio
R = ROOT / "runs/frontier_whole_message_r2"

def gens():
    ds = [pd.read_csv(p, keep_default_na=False) for p in sorted(R.glob("gens_*.csv"))]
    return pd.concat(ds, ignore_index=True)

def judgerun():
    g = gens(); inp = pd.read_csv(R / "inputs.csv", keep_default_na=False)
    keep = g[((g.draw == 0)) | ((g.arm == "A0") & (g.draw > 0))]
    keep = keep[keep.text != ""]
    recs = []
    for _, r in keep.iterrows():
        oid = hashlib.sha256(f"{r.generator}|{r.arm}|{r.draw}|{r.family_id}|{r.variant}|{r.channel}|{r.text}".encode()).hexdigest()[:16]
        recs.append(dict(output_id=oid, text=r.text, suggestion_idx=0, parse_ok=True, model=r.generator, prompt_id=r.arm, temperature=0.0 if r.draw == 0 else 0.7,
                         sample_idx=int(r.draw), dimension=r.dimension, split="hw", input_text=r.input_text, family_id=r.family_id, variant=r.variant, channel=r.channel))
    runio.write_jsonl(R / "outputs.jsonl", recs); print(len(recs), "records for the judge run;", keep.text.nunique(), "unique texts")

def m1_jobs(stage):
    g = gens(); inp = pd.read_csv(R / "inputs.csv", keep_default_na=False)
    ref = {(r.family_id, r.variant, r.channel): r.ref for _, r in inp.iterrows()}
    T = g[g.generator == "gpt-6.1-terra"]; J = []
    d0 = T[T.draw == 0]
    if stage in ("free_terra", "all"):
        J += [("free", r.input_text, r.text, None) for _, r in d0.iterrows() if r.text]
    if stage in ("ref_terra", "all"):
        sel = T[((T.draw == 0) & T.arm.isin(["A0", "A1", "A2", "A6"]))]
        J += [("ref", r.input_text, r.text, ref[(r.family_id, r.variant, r.channel)]) for _, r in sel.iterrows() if r.text]
    if stage in ("ref_b4", "all"):
        sel = T[(T.draw == 1) & (T.arm == "A2")]
        J += [("ref", r.input_text, r.text, ref[(r.family_id, r.variant, r.channel)]) for _, r in sel.iterrows() if r.text]
    if stage in ("free_others", "free_luna", "free_llama", "all"):
        for gname in {"free_luna": ["gpt-5.6-luna"], "free_llama": ["llama3.1-8b"]}.get(stage, ["gpt-5.6-luna", "llama3.1-8b"]):
            o = g[(g.generator == gname) & (g.draw == 0)]
            J += [("free", r.input_text, r.text, None) for _, r in o.iterrows() if r.text]
    seen = set(); out = []
    for j in J:
        if j not in seen: seen.add(j); out.append(j)
    return out

if __name__ == "__main__":
    if sys.argv[1] == "judgerun": judgerun()
    else:
        import frontier_whole_message_m1 as m1
        for st in (sys.argv[2:] or ["free_terra", "ref_terra", "free_others"]):
            J = m1_jobs(st); print(st, len(J), "jobs", flush=True); asyncio.run(m1.run(J, conc=3))
        print("M1DONE")
