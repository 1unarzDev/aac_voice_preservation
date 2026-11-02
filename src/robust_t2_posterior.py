"""T2: is the affirmative default Bayes-rational?  P(message negated | no negation word among its keywords).

    . .venv/bin/activate && python src/robust_t2_posterior.py

Stored data only (0 generation / 0 judge calls). Writes analysis/robust/t2_posterior/{report.md,summary.json,tables.csv}.

Ingredients
 * prevalence pi: detector labels on all 6,142 AACText messages (analysis/s1/message_cues.jsonl; detector polarity
   150/150 vs LLM first pass) and the uniform-random half of the elicitation sample (pi_incl = 300/4560).
 * keyword channel: POS-cap4 (crude compressor) and the Part 9 human keyword sets (analysis/elicitation/ratings.csv):
   d = P(keywords carry no cue | message has the cue)  (lenient 'lost' flag from the stored ratings).
 * f = P(keywords carry no cue | message lacks the cue), measured lexically on the typed keywords.
 * model behaviour: P0 outputs of runs/elic1 (4 models) on exactly those keyword inputs, general-dimension labels,
   Horvitz-Thompson weights 1/inclusion_prob (message level). The negation/politeness/act of the SOURCE is the detector label.
Bootstrap: 1,000 resamples of messages (stratified by sample type), seed 20261101.
"""
from __future__ import annotations
import json, re, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from robust_common import ROOT, SEED, outdir, write_json, pct, ci_str, md_table

OUT = outdir("t2_posterior"); B = 1000
NEG = re.compile(r"\b(?:not|no|never|none|nothing|nobody|nowhere|neither|nor|without|cannot|cant|dont|doesnt|didnt|wont|isnt|arent|wasnt|werent|couldnt|wouldnt|shouldnt|havent|hasnt|hadnt)\b|n't", re.I)
POL = re.compile(r"\b(?:please|pls|plz|thanks?|thank|sorry|excuse|pardon|appreciate|could|would|may)\b", re.I)
# speech-act cue words a keyword set could carry (question word / request marker / modal / imperative frame)
ACT = re.compile(r"\b(?:please|can|could|would|will|shall|let|lets|let's|why|what|where|when|who|whom|how|which|do|does|did|is|are|am|may|should|want|need)\b|\?", re.I)

# ------------------------------------------------------------------ corpus prevalence (all 6,142 messages)
corp = [json.loads(l) for l in open(ROOT / "analysis/s1/message_cues.jsonl")]
lab = pd.DataFrame([dict(id=c["id"], text=c["text"], kw=" ".join(c["keywords"]["pos_cap4"]) if isinstance(c["keywords"], dict) and "pos_cap4" in c["keywords"] else str(c["keywords"]),
                         **c["detector"]["labels"]) for c in corp])
lab["neg"] = lab.polarity.eq("negated"); lab["polite"] = lab.politeness.ne("none"); lab["nonstmt"] = lab.speech_act.ne("statement")
corpus = {k: float(lab[k].mean()) for k in ("neg", "polite", "nonstmt")}
cap4_f = {"neg": float((~lab[~lab.neg].kw.str.contains(NEG)).mean()), "polite": float((~lab[~lab.polite].kw.str.contains(POL)).mean())}

# ------------------------------------------------------------------ elicitation sample, unit = (message, keyword set)
msg = pd.read_csv(ROOT / "analysis/elicitation/messages.csv"); rat = pd.read_csv(ROOT / "analysis/elicitation/ratings.csv")
key = {j["item_id"]: j for j in map(json.loads, open(ROOT / "annotation/elicitation_key.jsonl"))}
msg["neg"] = [key[i]["detector_labels"]["polarity"] == "negated" for i in msg.item_id]
msg["polite"] = [key[i]["detector_labels"]["politeness"] != "none" for i in msg.item_id]
msg["nonstmt"] = [key[i]["detector_labels"]["speech_act"] != "statement" for i in msg.item_id]
msg["w"] = 1 / msg.inclusion_prob; msg["fam"] = "elic-" + msg.source_id
mi = msg.set_index("item_id")

units = []
for r in rat.itertuples():
    m = mi.loc[r.item_id]
    units.append(dict(item_id=r.item_id, fam=m.fam, channel="human_" + r.annotator, kw=str(r.keywords), neg=m.neg, polite=m.polite,
                      nonstmt=m.nonstmt, lost_neg=r.polarity_lenient_lost, lost_pol=r.politeness_lenient_lost, lost_act=r.speech_act_lenient_lost,
                      w=m.w, sample=m["sample"]))
for m in msg.itertuples():
    units.append(dict(item_id=m.item_id, fam=m.fam, channel="pos_cap4", kw=str(m.pos_cap4), neg=m.neg, polite=m.polite, nonstmt=m.nonstmt,
                      lost_neg=m.polarity_lenient_pos_loss, lost_pol=m.politeness_lenient_pos_loss, lost_act=m.speech_act_lenient_pos_loss,
                      w=m.w, sample=m.sample))
U = pd.DataFrame(units)
U["kw_neg"] = U.kw.str.contains(NEG); U["kw_pol"] = U.kw.str.contains(POL); U["kw_act"] = U.kw.str.contains(ACT)
U["nocue_neg"] = ~U.kw_neg; U["nocue_pol"] = ~U.kw_pol
# 'no cue' for the three dimensions: negation/politeness by lexicon; speech act by the rating flag when the message has a cue, else lexicon
U["nocue_act"] = np.where(U.nonstmt, U.lost_act.fillna(1).astype(bool), ~U.kw_act)

# model P0 outputs on those keyword inputs
sc = pd.read_parquet(ROOT / "runs/elic1/scored.parquet"); sc = sc[sc.prompt_id.eq("P0")][["family_id", "channel", "model", "polarity", "politeness", "speech_act", "text"]]
sc = sc.rename(columns={"family_id": "fam"})
sc["out_neg"] = sc.polarity.eq("negated"); sc["out_pol"] = sc.politeness.ne("none"); sc["out_nonstmt"] = ~sc.speech_act.eq("statement")
SC = sc.merge(U[["fam", "channel", "item_id", "neg", "polite", "nonstmt", "w", "sample", "nocue_neg", "nocue_pol", "nocue_act", "kw_neg", "kw_pol", "lost_neg", "lost_pol", "lost_act"]],
              on=["fam", "channel"], how="left")
assert len(SC) == 9600 and SC.item_id.notna().all()

DIMS = {"polarity": dict(src="neg", nocue="nocue_neg", out="out_neg", lost="lost_neg", prev="neg", f="neg"),
        "politeness": dict(src="polite", nocue="nocue_pol", out="out_pol", lost="lost_pol", prev="polite", f="polite"),
        "speech_act": dict(src="nonstmt", nocue="nocue_act", out="out_nonstmt", lost="lost_act", prev="nonstmt", f=None)}


def ht(x, w):
    return float((x * w).sum() / w.sum())


def stat(U, SC, d, chan, rng_idx=None):
    """All estimands for one dimension and channel family ('human' / 'pos_cap4')."""
    c = DIMS[d]
    sel = U.channel.eq("pos_cap4") if chan == "pos_cap4" else U.channel.str.startswith("human_")
    u = U[sel]; s = SC[SC.channel.eq("pos_cap4")] if chan == "pos_cap4" else SC[SC.channel.str.startswith("human_")]
    # message-weighted pooled over keyword sets (each message contributes equally across its sets via weight w per unit)
    src, noc = u[c["src"]].astype(bool), u[c["nocue"]].astype(bool)
    w = u.w
    post = ht((src & noc), w) / ht(noc, w) if ht(noc, w) > 0 else np.nan          # empirical P(source has cue | keywords lack cue)
    dloss = ht(u[src][c["lost"]].fillna(1).astype(float), w[src]) if src.any() else np.nan
    f_ = ht(noc[~src].astype(float), w[~src]) if (~src).any() else np.nan
    pi = ht(src.astype(float), w)
    # models
    ssrc, snoc, sout, sw = s[c["src"]].astype(bool), s[c["nocue"]].astype(bool), s[c["out"]].astype(bool), s.w
    out_given_nocue = ht(sout[snoc], sw[snoc]) if snoc.any() else np.nan           # model share outputting the cue-bearing value given no cue in keywords
    rev = ht((ssrc & snoc & ~sout), sw)                                              # silently reversed: cue in source, none in keywords, output lacks it
    miss_rate = ht((~sout[ssrc & snoc]).astype(float), sw[ssrc & snoc]) if (ssrc & snoc).any() else np.nan   # P(output lacks cue | source has cue, keywords lack it)
    fa = ht((~ssrc & sout), sw)                                                      # spurious: output asserts cue, source lacks it
    return dict(pi_frame=pi, d_loss=dloss, f_nocue_given_absent=f_, posterior_empirical=post, model_share_cue_given_nocue=out_given_nocue,
                model_miss_given_cue_lost=miss_rate, silent_reversal_per_1000=1000 * rev, spurious_cue_per_1000=1000 * fa,
                n_units=int(len(u)), n_messages=int(u.item_id.nunique()))


def boot_stats(U, SC, d, chan, rng):
    ids = {k: msg[msg["sample"].eq(k)].item_id.to_numpy() for k in ("random", "enriched")}
    allids = msg.item_id.to_numpy(); pos = {i: j for j, i in enumerate(allids)}
    ui = U.item_id.map(pos).to_numpy(); si = SC.item_id.map(pos).to_numpy(); rows = []
    for _ in range(B):
        mult = np.zeros(len(allids))
        for k, v in ids.items():
            np.add.at(mult, [pos[i] for i in rng.choice(v, len(v))], 1)
        ub = U.assign(w=U.w * mult[ui]); sb = SC.assign(w=SC.w * mult[si])
        rows.append(stat(ub[ub.w > 0], sb[sb.w > 0], d, chan))
    return pd.DataFrame(rows)


rng = np.random.default_rng(SEED)
rows = []; summ = {"corpus_prevalence_detector_6142": corpus, "pos_cap4_f_corpus": cap4_f, "seed": SEED, "n_boot": B}
KEYS = ["pi_frame", "d_loss", "f_nocue_given_absent", "posterior_empirical", "model_share_cue_given_nocue", "model_miss_given_cue_lost",
        "silent_reversal_per_1000", "spurious_cue_per_1000"]
for d in DIMS:
    for chan in ("human", "pos_cap4"):
        pt = stat(U, SC, d, chan); bs = boot_stats(U, SC, d, chan, rng)
        # formula-based posterior with corpus prevalence (all 6,142) and the same d, f (Bayes rule)
        pi_c = corpus[DIMS[d]["prev"]]; fF = pt["f_nocue_given_absent"]
        bayes = pi_c * pt["d_loss"] / (pi_c * pt["d_loss"] + (1 - pi_c) * fF)
        pt["posterior_bayes_corpus_pi"] = bayes
        pt["breakeven_cost_ratio"] = (1 - pt["posterior_empirical"]) / pt["posterior_empirical"]
        pt["queries_per_catch"] = 1 / pt["posterior_empirical"]
        row = dict(dimension=d, channel=chan) | pt
        for k in KEYS:
            row[k + "_lo"], row[k + "_hi"] = [float(x) for x in np.nanquantile(bs[k], [.025, .975])]
        rows.append(row)
T = pd.DataFrame(rows); T.to_csv(OUT / "tables.csv", index=False)

# random half only, unweighted check for polarity
rnd = U[U["sample"].eq("random") & U.channel.str.startswith("human_")]
chk = {"random_half_polarity_human": dict(n_messages=int(rnd.item_id.nunique()), negated_messages=int(rnd.drop_duplicates("item_id").neg.sum()),
       posterior_no_negation_word=float((rnd.neg & rnd.nocue_neg).sum() / rnd.nocue_neg.sum()),
       cases=int((rnd.neg & rnd.nocue_neg).sum()), of=int(rnd.nocue_neg.sum()))}
# per-model silent reversal, polarity, human keywords
pm = []
for m, g in SC[SC.channel.str.startswith("human_")].groupby("model"):
    pm.append(dict(model=m, silent_reversal_per_1000=1000 * ht((g.neg & g.nocue_neg & ~g.out_neg), g.w),
                   affirmative_share_given_no_neg_word=ht(~g.out_neg[g.nocue_neg], g.w[g.nocue_neg]),
                   miss_given_negated_and_dropped=ht(~g.out_neg[g.neg & g.nocue_neg], g.w[g.neg & g.nocue_neg])))
pm = pd.DataFrame(pm); pm.to_csv(OUT / "polarity_by_model_human_keywords.csv", index=False)
# prior hw1/W-C bare affirmative shares for comparison (stored, not recomputed here)
p3 = {"W-C_P3_affirmative_share": json.load(open(ROOT / "analysis/r2c/primary.json")) if (ROOT / "analysis/r2c/primary.json").exists() else None}
hw = json.load(open(ROOT / "analysis/hw1/summary.json"))["P3_affirmative_share"]
wcp = p3["W-C_P3_affirmative_share"]
wcshare = None
if wcp:
    for k in ("bare_affirmative_share", "p3_affirmative_share"):
        if k in wcp: wcshare = wcp[k]
summ |= {"table": T.to_dict("records"), "random_half_check": chk, "per_model_polarity_human_keywords": pm.to_dict("records"),
         "hw1_P3_affirmative_share": {k: hw[k] for k in ("estimate", "ci_low", "ci_high", "n")}, "wc_primary_keys": sorted(wcp.keys())[:30] if wcp else None}
write_json(OUT / "summary.json", summ)


def g(d, ch): return T[(T.dimension == d) & (T.channel == ch)].iloc[0]


def rng_s(r, k, nd=1, per=False):
    f = (lambda x: f"{x:.1f}") if per else (lambda x: pct(x, nd))
    return f"{f(r[k])}{'' if per else '%'} [{f(r[k+'_lo'])}, {f(r[k+'_hi'])}]"


pn_h, pn_c = g("polarity", "human"), g("polarity", "pos_cap4")
L = ["# T2: is 'affirmative' the Bayes-preferred guess? Posterior of negation given no negation word in the keywords", "",
     "Stored data only: 0 generation / 0 judge calls. Script `src/robust_t2_posterior.py`; tables `tables.csv`, `polarity_by_model_human_keywords.csv`; numbers in `summary.json`.", "",
     "## Publishable paragraph (polarity)", "",
     f"Defaulting to *affirmative* when a keyword string contains no negation word is the Bayes-preferred guess on real AAC-style text, so the 99% affirmative share of the models is not by itself an error. "
     f"In AACText, {pct(corpus['neg'])}% of {len(lab):,} messages are negated (detector, 150/150 against an LLM first pass). "
     f"A crude content-word compressor (POS-cap4) deletes the negation in {pct(pn_c['d_loss'],0)}% of negated messages, and humans typing keywords for the same messages keep it "
     f"{pct(1-pn_h['d_loss'])}% of the time (so they drop it {rng_s(pn_h,'d_loss')}). Among keyword strings with no negation word, the share whose source message was negated is therefore "
     f"{rng_s(pn_h,'posterior_empirical')} for human keywords (Horvitz-Thompson over the elicitation frame; {pct(pn_h['posterior_bayes_corpus_pi'])}% by Bayes' rule with the corpus prevalence; "
     f"{pct(chk['random_half_polarity_human']['posterior_no_negation_word'])}% in the unweighted random half) and {rng_s(pn_c,'posterior_empirical')} for POS-cap4 ({pct(pn_c['posterior_bayes_corpus_pi'])}% with the corpus prevalence). "
     f"Guessing affirmative is right {pct(1-pn_h['posterior_empirical'])}% (human keywords) / {pct(1-pn_c['posterior_empirical'])}% (POS-cap4) of the time. "
     f"The models output an affirmative sentence for {pct(1-pn_h['model_share_cue_given_nocue'])}% (human keywords) and {pct(1-pn_c['model_share_cue_given_nocue'])}% (POS-cap4) of such inputs: "
     f"the direction of the default is the rational one, but the models are more confident than the evidence ({pct(pn_h['posterior_empirical']-pn_h['model_share_cue_given_nocue'])} and {pct(pn_c['posterior_empirical']-pn_c['model_share_cue_given_nocue'])} points fewer negated outputs than the posterior implies), "
     f"so a frequency argument defends the default but not its certainty. The harm is the asymmetric cost: of every 1,000 messages, about "
     f"{pn_h['silent_reversal_per_1000']:.0f} [{pn_h['silent_reversal_per_1000_lo']:.0f}, {pn_h['silent_reversal_per_1000_hi']:.0f}] negated messages are silently reversed into an affirmative sentence when the user types the keywords unaided, "
     f"and {pn_c['silent_reversal_per_1000']:.0f} [{pn_c['silent_reversal_per_1000_lo']:.0f}, {pn_c['silent_reversal_per_1000_hi']:.0f}] with a POS-cap4 compressor, while a spurious negation is introduced in only {pn_h['spurious_cue_per_1000']:.1f} per 1,000. "
     f"The affirmative guess breaks even with the opposite guess only if a reversed negation costs less than {pn_h['breakeven_cost_ratio']:.0f} (human keywords) or {pn_c['breakeven_cost_ratio']:.0f} (POS-cap4) times a spurious one; "
     f"no sentence-level default can remove that exposure, but a prompt (a [NOT] chip, or a confirmation when no negation word is present) would have to be shown on about {pn_h['queries_per_catch']:.0f} (human keywords) / {pn_c['queries_per_catch']:.0f} (POS-cap4) inputs per reversal it prevents.", "",
     "## Estimates by dimension and keyword channel", "",
     "pi = frame prevalence of the cue in the source message (HT-weighted elicitation sample); d = P(keywords carry no cue | source has cue); post = P(source has cue | keywords carry no cue); "
     "model share = share of P0 outputs (4 models) that assert the cue-bearing value given keywords with no cue; reversal/1000 = source has cue, keywords lack it, output lacks it, per 1,000 messages; "
     "spurious/1000 = output asserts the cue though the source lacks it. 95% message-bootstrap CIs (stratified by sample type).", "",
     "| dimension | channel | pi | d (cue dropped) | P(source has cue \\| no cue in keywords) | Bayes w/ corpus pi | model share asserting cue \\| no cue | silent reversal /1,000 | spurious /1,000 | break-even cost ratio | queries per catch |",
     "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in T.itertuples():
    r = T[(T.dimension == r.dimension) & (T.channel == r.channel)].iloc[0]
    L.append(f"| {r.dimension} | {r.channel} | {rng_s(r,'pi_frame')} | {rng_s(r,'d_loss')} | {rng_s(r,'posterior_empirical')} | {pct(r.posterior_bayes_corpus_pi)}% | "
             f"{rng_s(r,'model_share_cue_given_nocue')} | {rng_s(r,'silent_reversal_per_1000',per=True)} | {rng_s(r,'spurious_cue_per_1000',per=True)} | {r.breakeven_cost_ratio:.1f}:1 | {r.queries_per_catch:.1f} |")
ps, pp = g("speech_act", "human"), g("politeness", "human")
pps, ppc = g("speech_act", "pos_cap4"), g("politeness", "pos_cap4")
def cmp(r):
    gap = r["posterior_empirical"] - r["model_share_cue_given_nocue"]
    return (f"models assert the cue-bearing value on {rng_s(r,'model_share_cue_given_nocue')} of such inputs against a posterior of {rng_s(r,'posterior_empirical')} "
            f"({'fewer' if gap > 0 else 'more'} than the posterior by {abs(gap)*100:.1f} points)")


L += ["", "## Politeness and speech act", "",
      f"**Politeness.** {pct(corpus['polite'])}% of AACText messages carry an explicit polite word (please/could you/thanks/sorry). Given keywords with no polite word, the source was polite in "
      f"{rng_s(pp,'posterior_empirical')} (human) and {rng_s(ppc,'posterior_empirical')} (POS-cap4, which keeps most 'please'): plain is the Bayes-preferred guess, and for human keywords {cmp(pp)}; for POS-cap4 {cmp(ppc)}. "
      f"Politeness the user did type but the keywords dropped is lost for about {pp['silent_reversal_per_1000']:.0f} per 1,000 messages (human keywords); the break-even cost ratio is {pp['breakeven_cost_ratio']:.0f}:1, so the asymmetry is far milder than for negation. "
      f"The opposite error (politeness added that the source lacked; +7.6 pp in hw1 P2 under full input) is a separate false-positive channel: {pp['spurious_cue_per_1000']:.0f} per 1,000 messages here (outputs with any polite marker; the source being plain is the majority case).", "",
      f"**Speech act.** {pct(corpus['nonstmt'])}% of AACText messages are not statements (detector). Given keywords that carry no speech-act cue, the source was a question/request/other in {rng_s(ps,'posterior_empirical')} (human) and {rng_s(pps,'posterior_empirical')} (POS-cap4), "
      f"so 'statement' is at best a coin-flip guess; for human keywords {cmp(ps)}; for POS-cap4 {cmp(pps)}. "
      f"On this dimension the models' statement default is MORE extreme than the posterior supports, with {ps['silent_reversal_per_1000']:.0f} per 1,000 messages having their act reversed or flattened (human keywords). Unlike negation there is no single safe default and the break-even cost ratio is about {ps['breakeven_cost_ratio']:.1f}:1.", "",
      "## Per-model silent reversal, polarity, human keywords", "", md_table(pm), "",
      "## Checks", "",
      f"* Random half only (unweighted, {chk['random_half_polarity_human']['n_messages']} messages): P(negated | no negation word) = {chk['random_half_polarity_human']['cases']}/{chk['random_half_polarity_human']['of']} = {pct(chk['random_half_polarity_human']['posterior_no_negation_word'])}%.",
      f"* hw1 P3 (design-balanced pairs, bare): affirmative {pct(hw['estimate'],2)}% [{pct(hw['ci_low'],2)}, {pct(hw['ci_high'],2)}]; that share is not comparable with the posterior because the pair design makes the true rate 50%; here the real-text posterior is the right benchmark.", "",
      "## Caveats", "",
      "* Source polarity, politeness and speech act are detector labels (polarity 150/150 vs LLM first pass; the others less validated), not human gold. Part 9 'lost' flags are the stored lenient ratings.",
      "* The elicitation frame (4,560 texts) excludes messages under 3 words, duplicates and W-B/W-C seeds; short messages ('No.', 'No thanks') are probably more often negated, so frame HT prevalence and the 6,142-message corpus prevalence differ slightly; both are shown.",
      "* The HT frame prevalences (polarity 11.4%, speech act 61.7%) exceed the corpus detector prevalences (8.6%, 48.4%): the enriched-stratum inclusion probabilities are conditional on the random draw and not exact. Treat the HT posterior as the upper and the Bayes-with-corpus-prevalence value as the lower end of the plausible range (they bracket the unweighted random half).",
      "* A negation word in keywords is a lexical test. Humans sometimes encode negation in a content word ('refuse', 'stop'); 'lost' flags (stored ratings) are the lenient human judgement and are used for d; f uses the lexicon.",
      "* Speech-act 'no cue' is the stored lenient 'lost' flag when the source has a cue and a question/request word lexicon otherwise: a proxy.",
      "* Prompt licence (T1: `[NOT]` legend in every prompt) is untested here; this analysis says what the rational default is, not what the model's reason for it is.",
      "* Model outputs are P0 greedy, one draw, 4 models; elic1 arbitrated labels (D-055)."]
(OUT / "report.md").write_text("\n".join(L) + "\n")
print("\n".join(L[:12]))
