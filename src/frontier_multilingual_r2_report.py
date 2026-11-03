"""Render round-2 tables from summary_r2.json (+ validation, gate, naturalness) into analysis/frontier/multilingual/round2_auto_tables.md. Re-run after any new generation."""
import json, sys
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / "analysis/frontier/multilingual"
S = json.load(open(OUT / "summary_r2.json"))
def p(x, d=0):
    return "NA" if x is None else f"{100*x:.{d}f}%"
def ci(a, d=0):
    return "NA" if not a or a[0] is None else f"{100*a[0]:.{d}f}-{100*a[1]:.{d}f}"
def pe(t, d=0):  # [est,[lo,hi]]
    return f"{p(t[0], d)} ({ci(t[1], d)})"
M = S["models"]; L = ["de", "es", "fr"]; o = []
o.append(f"# Round-2 auto tables (models with data: {', '.join(M)}; rows {S['n_rows']})\n")
o.append("## E1 register commitment, bare, unconditional (P(no address) | P(single register | address) | n address / n outputs | V share among T/V)\n")
o.append("| scope | " + " | ".join(l.upper() for l in L) + " |\n|---|---|---|---|")
for sc in ["pooled"] + M:
    cells = []
    for l in L:
        e = S["E1_E2_register_bare"][f"{sc}|{l}"]
        cells.append(f"none {p(e['P_no_address'][0])} / single {p(e['P_single_given_address'][0])} / {e['n_address']}of{e['n_outputs']} / V {p(e['V_share'][0])} (n={e['n_TV']})")
    o.append(f"| {sc} | " + " | ".join(cells) + " |")
o.append("\n## E2 language contrasts (V-share difference, cluster bootstrap CI, Holm p)\n| test | diff | 95% CI | p_holm | confirmed (Holm<.05 and >=30pp) |\n|---|---|---|---|---|")
for k, v in S["E2_language_contrasts_holm"].items():
    o.append(f"| {k} | {100*v['est']:.1f} pp | {100*v['ci'][0]:.0f} to {100*v['ci'][1]:.0f} | {v['p_holm']:.3f} | {v['language_effect_confirmed']} |")
o.append("\nModel range of V-share within language: " + "; ".join(f"{l}: {100*S['E2_model_range'][l]['range']['est']:.0f} pp (CI {100*S['E2_model_range'][l]['range']['ci'][0]:.0f}-{100*S['E2_model_range'][l]['range']['ci'][1]:.0f})" for l in L))
o.append("\n## E3 polarity default vs matched English (P(affirmative | committed) / P(negated | all) / diff vs EN [CI])\n| draw | scope | EN | DE | ES | FR |\n|---|---|---|---|---|---|")
for tag in ("greedy", "sampled"):
    for sc in ["pooled"] + M:
        cells = []
        for l in ["en"] + L:
            e = S["E3_polarity_default"][f"{tag}|{sc}|{l}"]
            d = e.get("diff_vs_english")
            cells.append(f"{p(e['P_aff_committed'][0],1)} / neg {p(e['P_neg_all'][0],1)}" + (f" / d {100*d['est']:.1f} [{100*d['ci'][0]:.1f},{100*d['ci'][1]:.1f}]" if d else "") + f" n={e['n']}")
        o.append(f"| {tag} | {sc} | " + " | ".join(cells) + " |")
o.append("\n## E3b pronoun-address vs English (P(you) EN; target pronoun-address; diff [CI])\n| scope | DE | ES | FR |\n|---|---|---|---|")
for sc in ["pooled"] + M:
    o.append(f"| {sc} | " + " | ".join(f"EN {p(S['E3b_pronoun_address_vs_english'][f'{sc}|{l}']['P_you_english'])} / {l.upper()} {p(S['E3b_pronoun_address_vs_english'][f'{sc}|{l}']['P_pronoun_target'])} / d {100*S['E3b_pronoun_address_vs_english'][f'{sc}|{l}']['est']:.0f} [{100*S['E3b_pronoun_address_vs_english'][f'{sc}|{l}']['ci'][0]:.0f},{100*S['E3b_pronoun_address_vs_english'][f'{sc}|{l}']['ci'][1]:.0f}]" for l in L) + " |")
o.append("\n## E4 cue restoration (B families): negated rate restored / bare / plain word; gain CI lower bound\n| scope | EN | DE | ES | FR |\n|---|---|---|---|---|")
for sc in ["pooled"] + M:
    cells = []
    for l in ["en"] + L:
        e = S["E4_cue_restoration"][f"{sc}|{l}"]
        cells.append(f"{p(e['restored_B_negated'][0])} / {p(e['bare_negated'][0])} / plain {p(e['plain_neg_negated'][0])}; gain lo {100*e['gain_restored_minus_bare']['ci'][0]:.0f} pp")
    o.append(f"| {sc} | " + " | ".join(cells) + " |")
o.append("\nModels meeting the >=50 pp lower-bound criterion: " + "; ".join(f"{l}: {len(v)}/{len(M)}" for l, v in S["E4_models_meeting_50pp"].items()))
o.append("\nInstrument agreement (direct vs translate-then-English), positive agreement on the NEGATED class (restored B) and the affirmative class (restored A):")
for l, v in S["E4_instrument_agreement"].items():
    a, b = v["negated_class_on_restored_B"], v["affirmative_class_on_restored_A"]
    o.append(f"- {l.upper()}: negated PA {a['pos_agreement']:.3f} (direct {a['n_direct']}, route {a['n_route']}, both {a['n_both']}, n={a['n']}); affirmative PA {b['pos_agreement']:.3f} (n={b['n']})")
o.append("\n## E5 register cues, pooled (match among address / address rate / match of all)\n| lang, requested | chip | plain | ctx | plain_x (legend-eq.) | ctx_x |\n|---|---|---|---|---|---|")
for l in L:
    for nm in ("formal", "informal"):
        D = S["E5_register_cues"][f"pooled|{l}|{nm}"]
        o.append(f"| {l.upper()} {nm} | " + " | ".join(f"{p(D[a]['match_among_address'][0])} / {p(D[a]['address_rate'][0])} / {p(D[a]['match_of_all'][0])}" for a in D) + " |")
o.append("\nChip minus legend-equalised cues, match of all outputs (paired, pooled):")
for l in L:
    for nm in ("formal", "informal"):
        D = S["E5_register_cues"][f"pooled|{l}|{nm}"]
        c = D[f"chip_{nm}"]
        o.append(f"- {l.upper()} {nm}: chip-plain_x {100*c[f'minus_plain_{nm}_x_match_of_all']['est']:.0f} pp [{100*c[f'minus_plain_{nm}_x_match_of_all']['ci'][0]:.0f},{100*c[f'minus_plain_{nm}_x_match_of_all']['ci'][1]:.0f}]; chip-ctx_x {100*c[f'minus_ctx_{nm}_x_match_of_all']['est']:.0f} pp [{100*c[f'minus_ctx_{nm}_x_match_of_all']['ci'][0]:.0f},{100*c[f'minus_ctx_{nm}_x_match_of_all']['ci'][1]:.0f}]")
o.append("\nFR-informal chip outputs by model: " + json.dumps(S["FR_informal_chip_failure"], ensure_ascii=False))
o.append("\n## E6 keyword-condition controls (V share among T/V; n in parentheses; pooled address rate)\n| lang | condition | pooled V | address rate | " + " | ".join(M) + " | model range |\n|---|---|---|---|" + "---|" * (len(M) + 1))
for k, v in S["E6_keyword_conditions"].items():
    l, c = k.split("|")
    rg = v["range"]
    o.append(f"| {l} | {c} | {pe(v['pooled_V_share'])} | {p(v['pooled_address_rate'][0])} | " + " | ".join(f"{p(v['per_model'][m]['V_share'])} (n={v['per_model'][m]['n_TV']})" for m in M) + f" | {('NA' if not rg else f'{100*rg['est']:.0f} pp ({100*rg['ci'][0]:.0f}-{100*rg['ci'][1]:.0f})')} |")
o.append("\n## E9 policies. Polarity at pi_neg=2.7% (silent reversals per 1,000; taps per 1,000)\n")
pol = S["E9_polarity_policies"]
pn = sorted({k.split("|")[2] for k in pol if k.count("|") == 2 and not k.split("|")[2].startswith("entropy_minus") and k.split("|")[2] != "entropy_ask_rate"})
o.append("| policy | " + " | ".join(l.upper() for l in ["en"] + L) + " |\n|---|---|---|---|---|")
for k in pn:
    cells = []
    for l in ["en"] + L:
        e = pol.get(f"pol|{l}|{k}")
        cells.append("NA" if not e else f"{e['silent_reversals_per_1000@pi=2.7%'][0]:.1f} [{e['silent_reversals_per_1000@pi=2.7%'][1][0]:.1f},{e['silent_reversals_per_1000@pi=2.7%'][1][1]:.1f}] ; taps {1000*e['taps_per_message']:.0f}")
    o.append(f"| {k} | " + " | ".join(cells) + " |")
o.append("\nEntropy-ask rate (polarity): " + ", ".join(f"{l}: {p(pol[f'pol|{l}|entropy_ask_rate'],1)}" for l in ["en"] + L))
o.append("\n## E9 register at pi_V=0.5 (mismatch per 1,000 [CI]; taps per 1,000)\n| policy | DE | ES (expl.) | FR |\n|---|---|---|---|")
rp = S["E9_register_policies"]
names = []
for k in rp:
    n = k.split("|")[2]
    if n not in names and "minus" not in n:
        names.append(n)
for n in names:
    o.append(f"| {n} | " + " | ".join((lambda e: "NA" if not e else f"{e['mismatch_per_1000'][0]:.0f} [{e['mismatch_per_1000'][1][0]:.0f},{e['mismatch_per_1000'][1][1]:.0f}] ; taps {e['taps_per_1000']:.0f}")(rp.get(f"reg|{l}|{n}|piV=0.5")) for l in L) + " |")
o.append("\nAsk-if-address minus random-ask at matched taps (mismatch fraction, paired CI): " + "; ".join(f"{l}: {100*rp[f'reg|{l}|ask_if_address_minus_random_matched|piV=0.5']['est']:.1f} pp [{100*rp[f'reg|{l}|ask_if_address_minus_random_matched|piV=0.5']['ci'][0]:.1f},{100*rp[f'reg|{l}|ask_if_address_minus_random_matched|piV=0.5']['ci'][1]:.1f}]" for l in L))
o.append("\nG1 written cue: " + json.dumps(S["G1_written_cue"]))
for fn, title in (("r2_detector_validation.json", "E7 detector validation"), ("r2_naturalness_summary.json", "E10 naturalness"),):
    if (OUT / fn).exists():
        d = json.load(open(OUT / fn))
        o.append(f"\n## {title}\n```\n{json.dumps(d if 'valid' not in fn else {l: {k: v for k, v in x.items() if k != 'confusion'} for l, x in d.items()}, indent=1)[:5000]}\n```")
if (OUT / "r2_strict_gate.json").exists():
    d = json.load(open(OUT / "r2_strict_gate.json"))
    o.append(f"\n## E8 strict gate (second back-translator: {d['second_back_translator']})\n" + "\n".join(f"- {k}: {v}" for k, v in d["survival"].items()))
open(OUT / "round2_auto_tables.md", "w").write("\n".join(o) + "\n")
print("ok")
