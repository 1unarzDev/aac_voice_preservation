"""Build the judge/attribution fixture: 6 probe families (one per critical dimension),
~50 hand-made output occurrences (~43 unique texts) with hand gold labels.

Writes:
  tests/fixtures/probes_fixture.jsonl          SPEC item format
  runs/fixture/unique_outputs.jsonl            {output_id, text}
  runs/fixture/exploded.jsonl                  one row per (request, suggestion) -> output_id
  tests/fixtures/fixture_gold.jsonl            my hand labels per (output_id, family_id, input)
Run: python tests/make_fixture.py
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys  # noqa: E402
sys.path.insert(0, str(ROOT / "src"))
from runio import text_key  # noqa: E402
FAM = [
 dict(family_id="pol-01", dimension="polarity", split="pilot", context=None,
      variants={"A": dict(source="I don't want to go to the party tonight.", critical_value="negated",
                          chips=["[NOT]"], all_chips=["[NOT]", "[I]"]),
                "B": dict(source="I want to go to the party tonight.", critical_value="affirmative",
                          chips=["[YES]"], all_chips=["[YES]", "[I]"])},
      bare="want go party", noncritical="tonight",
      critical_options=["negated", "affirmative", "unclear/mixed"]),
 dict(family_id="role-01", dimension="agent", split="pilot", context=None,
      variants={"A": dict(source="I need to call grandma today.", critical_value="speaker",
                          chips=["[I]"], all_chips=["[I]"]),
                "B": dict(source="You need to call grandma today.", critical_value="addressee",
                          chips=["[YOU]"], all_chips=["[YOU]"])},
      bare="need call grandma", noncritical="today",
      critical_options=["speaker", "addressee", "we/joint", "third party", "unclear/mixed"]),
 dict(family_id="cert-01", dimension="certainty", split="pilot", context=None,
      variants={"A": dict(source="Maybe the bus is late today.", critical_value="hedged/uncertain",
                          chips=["[MAYBE]"], all_chips=["[MAYBE]", "[THEY]"]),
                "B": dict(source="The bus is late today.", critical_value="plain assertion",
                          chips=["[SURE]"], all_chips=["[SURE]", "[THEY]"])},
      bare="bus late", noncritical="today",
      critical_options=["plain assertion", "hedged/uncertain", "strongly certain/emphatic", "unclear/mixed"]),
 dict(family_id="act-01", dimension="speech_act", split="pilot", context=None,
      variants={"A": dict(source="Is dinner ready now?", critical_value="question",
                          chips=["[?]"], all_chips=["[?]", "[THEY]"]),
                "B": dict(source="Dinner is ready now.", critical_value="statement",
                          chips=["[TELL]"], all_chips=["[TELL]", "[THEY]"])},
      bare="dinner ready", noncritical="now",
      critical_options=["statement", "question", "request/command", "refusal", "acceptance", "offer/suggestion", "unclear/mixed"]),
 dict(family_id="polite-01", dimension="politeness", split="pilot", context=None,
      variants={"A": dict(source="Please open the window again.", critical_value="polite",
                          chips=["[PLEASE]"], all_chips=["[ASK]", "[YOU]", "[PLEASE]"]),
                "B": dict(source="Open the window again.", critical_value="plain",
                          chips=["[PLAIN]"], all_chips=["[ASK]", "[YOU]", "[PLAIN]"])},
      bare="open window", noncritical="again",
      critical_options=["polite", "plain", "unclear/mixed"]),
 dict(family_id="time-01", dimension="time_quantity", split="pilot", context=None,
      variants={"A": dict(source="I went to the park with mom.", critical_value="past",
                          chips=["[PAST]"], all_chips=["[PAST]", "[I]"]),
                "B": dict(source="I will go to the park with mom.", critical_value="later",
                          chips=["[LATER]"], all_chips=["[LATER]", "[I]"])},
      bare="go park", noncritical="mom",
      critical_options=["past", "now", "later", "unclear/mixed"]),
]
F = {f["family_id"]: f for f in FAM}


def visible(fam, var, ch):
    f, v = F[fam], F[fam]["variants"][var]
    return {"bare": f["bare"], "noncrit": f"{f['bare']} {f['noncritical']}",
            "chip1": " ".join(v["chips"] + [f["bare"]]),
            "chipall": " ".join(v["all_chips"] + [f["bare"]]),
            "full": v["source"]}[ch]

# (family, variant, channel, model, prompt, [texts]) ; gold per text:
# crit | polarity | speech_act | agent | certainty | politeness | added_content
N, Q, R = "n/a (question/request)", "question", "request/command"
SOFT = "softened request (could you/would you mind)"
ROWS = [
 ("pol-01", "A", "bare", "qwen2.5-7b", "P0", [("I want to go to the party.", "affirmative|affirmative|statement|speaker|plain assertion|none|no")]),
 ("pol-01", "A", "bare", "llama3.1-8b", "P0", [("I really want to go to the party tonight!", "affirmative|affirmative|statement|speaker|strongly certain/emphatic|none|yes")]),
 ("pol-01", "A", "chip1", "qwen2.5-7b", "P0", [("I want to go to the party.", "affirmative|affirmative|statement|speaker|plain assertion|none|no")]),
 ("pol-01", "A", "chip1", "llama3.1-8b", "P0", [("I don't want to go to the party.", "negated|negated|statement|speaker|plain assertion|none|no")]),
 ("pol-01", "A", "full", "gpt-6.1-terra", "P0", [("I don't want to go to the party tonight.", "negated|negated|statement|speaker|plain assertion|none|no")]),
 ("pol-01", "B", "chip1", "gpt-6.1-terra", "P0", [("Yes, I want to go to the party.", "affirmative|affirmative|statement|speaker|plain assertion|none|no")]),
 ("pol-01", "A", "bare", "gpt-6.1-terra", "P2", [("I want to go to the party.", "affirmative|affirmative|statement|speaker|plain assertion|none|no"),
                                               ("I don't want to go to the party.", "negated|negated|statement|speaker|plain assertion|none|no"),
                                               ("Do you want to go to the party?", f"affirmative|affirmative|offer/suggestion|addressee|{N}|none|no")]),
 ("pol-01", "B", "noncrit", "qwen2.5-7b", "P0", [("Maybe I'll go to the party tonight.", "affirmative|affirmative|statement|speaker|hedged/uncertain|none|no")]),
 ("pol-01", "A", "bare", "qwen2.5-7b", "P1", [("I'm not sure about going to the party.", "unclear/mixed|mixed/unclear|statement|speaker|hedged/uncertain|none|no")]),
 ("pol-01", "B", "chipall", "qwen2.5-7b", "P0", [("", None)]),   # non-completion
 ("role-01", "A", "bare", "qwen2.5-7b", "P0", [("I need to call grandma.", "speaker|affirmative|statement|speaker|plain assertion|none|no")]),
 ("role-01", "B", "bare", "llama3.1-8b", "P0", [("I need to call grandma.", "speaker|affirmative|statement|speaker|plain assertion|none|no")]),
 ("role-01", "B", "chip1", "qwen2.5-7b", "P0", [("You need to call grandma.", "addressee|affirmative|statement|addressee|plain assertion|none|no")]),
 ("role-01", "B", "chip1", "llama3.1-8b", "P0", [("I need to call grandma today.", "speaker|affirmative|statement|speaker|plain assertion|none|yes")]),
 ("role-01", "B", "chipall", "gpt-6.1-terra", "P0", [("Can you call grandma for me, please?", f"addressee|affirmative|{R}|addressee|{N}|please|no")]),
 ("role-01", "A", "full", "gpt-6.1-terra", "P0", [("I need to call grandma today.", "speaker|affirmative|statement|speaker|plain assertion|none|no")]),
 ("role-01", "A", "bare", "gpt-6.1-terra", "P2", [("I need to call grandma.", "speaker|affirmative|statement|speaker|plain assertion|none|no"),
                                                ("Can you call grandma?", f"addressee|affirmative|{R}|addressee|{N}|none|no"),
                                                ("We should call grandma.", "we/joint|affirmative|offer/suggestion|we/joint|plain assertion|none|no")]),
 ("cert-01", "A", "bare", "qwen2.5-7b", "P0", [("The bus is late today.", "plain assertion|affirmative|statement|third party|plain assertion|none|yes")]),
 ("cert-01", "A", "bare", "llama3.1-8b", "P0", [("The bus might be late.", "hedged/uncertain|affirmative|statement|third party|hedged/uncertain|none|no")]),
 ("cert-01", "A", "chip1", "qwen2.5-7b", "P0", [("The bus is late.", "plain assertion|affirmative|statement|third party|plain assertion|none|no")]),
 ("cert-01", "A", "chip1", "llama3.1-8b", "P0", [("Maybe the bus is late.", "hedged/uncertain|affirmative|statement|third party|hedged/uncertain|none|no")]),
 ("cert-01", "B", "chip1", "gpt-6.1-terra", "P0", [("The bus is definitely late.", "strongly certain/emphatic|affirmative|statement|third party|strongly certain/emphatic|none|no")]),
 ("cert-01", "B", "noncrit", "qwen2.5-7b", "P0", [("I think the bus is late today.", "hedged/uncertain|affirmative|statement|third party|hedged/uncertain|none|no")]),
 ("cert-01", "A", "full", "gpt-6.1-terra", "P1", [("Maybe the bus is late today.", "hedged/uncertain|affirmative|statement|third party|hedged/uncertain|none|no")]),
 ("cert-01", "B", "bare", "gpt-6.1-terra", "P2", [("The bus is late.", "plain assertion|affirmative|statement|third party|plain assertion|none|no"),
                                                ("Is the bus late?", f"unclear/mixed|affirmative|question|third party|{N}|none|no"),
                                                ("The bus might be late because of the snow.", "hedged/uncertain|affirmative|statement|third party|hedged/uncertain|none|yes")]),
 ("act-01", "A", "bare", "qwen2.5-7b", "P0", [("Dinner is ready.", "statement|affirmative|statement|third party|plain assertion|none|no")]),
 ("act-01", "A", "bare", "llama3.1-8b", "P0", [("Is dinner ready?", f"question|affirmative|question|third party|{N}|none|no")]),
 ("act-01", "A", "chip1", "llama3.1-8b", "P0", [("Dinner is ready now.", "statement|affirmative|statement|third party|plain assertion|none|yes")]),
 ("act-01", "A", "chipall", "gpt-6.1-terra", "P0", [("Is dinner ready yet?", f"question|affirmative|question|third party|{N}|none|no")]),
 ("act-01", "B", "chip1", "qwen2.5-7b", "P0", [("Dinner is ready now, everyone.", "statement|affirmative|statement|third party|plain assertion|none|yes")]),
 ("act-01", "B", "full", "gpt-6.1-terra", "P0", [("Dinner is ready now.", "statement|affirmative|statement|third party|plain assertion|none|no")]),
 ("act-01", "A", "noncrit", "qwen2.5-7b", "P0", [("Is dinner ready now?", f"question|affirmative|question|third party|{N}|none|no")]),
 ("act-01", "A", "bare", "gemma3-4b", "P0", [("Can I have dinner now?", f"question|affirmative|question|speaker|{N}|none|yes")]),
 ("polite-01", "B", "bare", "gemma3-4b", "P1", [("Can you open the window?", f"plain|affirmative|{R}|addressee|{N}|none|no")]),
 ("polite-01", "B", "bare", "qwen2.5-7b", "P0", [("Please open the window.", f"polite|affirmative|{R}|addressee|{N}|please|no")]),
 ("polite-01", "B", "bare", "llama3.1-8b", "P0", [("Could you open the window?", f"polite|affirmative|{R}|addressee|{N}|{SOFT}|no")]),
 ("polite-01", "B", "chip1", "qwen2.5-7b", "P0", [("Please open the window.", f"polite|affirmative|{R}|addressee|{N}|please|no")]),
 ("polite-01", "B", "chip1", "gpt-6.1-terra", "P0", [("Open the window.", f"plain|affirmative|{R}|addressee|{N}|none|no")]),
 ("polite-01", "A", "chip1", "llama3.1-8b", "P0", [("Open the window please, it's hot in here.", f"polite|affirmative|{R}|addressee|{N}|please|yes")]),
 ("polite-01", "B", "noncrit", "gpt-6.1-terra", "P1", [("Open the window again.", f"plain|affirmative|{R}|addressee|{N}|none|no")]),
 ("polite-01", "A", "full", "gpt-6.1-terra", "P0", [("Please open the window again.", f"polite|affirmative|{R}|addressee|{N}|please|no")]),
 ("polite-01", "A", "bare", "gemma3-4b", "P0", [("Sorry to bother you, but would you mind opening the window?", f"polite|affirmative|{R}|addressee|{N}|{SOFT}|no")]),
 ("time-01", "A", "bare", "qwen2.5-7b", "P0", [("I went to the park.", "past|affirmative|statement|speaker|plain assertion|none|no")]),
 ("time-01", "A", "bare", "llama3.1-8b", "P0", [("I will go to the park with mom.", "later|affirmative|statement|speaker|plain assertion|none|yes")]),
 ("time-01", "A", "chip1", "llama3.1-8b", "P0", [("I will go to the park.", "later|affirmative|statement|speaker|plain assertion|none|no")]),
 ("time-01", "B", "chip1", "qwen2.5-7b", "P0", [("I'll go to the park later.", "later|affirmative|statement|speaker|plain assertion|none|no")]),
 ("time-01", "A", "noncrit", "gpt-6.1-terra", "P0", [("I went to the park with mom.", "past|affirmative|statement|speaker|plain assertion|none|no")]),
 ("time-01", "A", "full", "gpt-6.1-terra", "P0", [("I went to the park with mom.", "past|affirmative|statement|speaker|plain assertion|none|no")]),
 ("time-01", "B", "bare", "gpt-6.1-terra", "P2", [("I went to the park.", "past|affirmative|statement|speaker|plain assertion|none|no"),
                                                ("I'm going to the park later.", "later|affirmative|statement|speaker|plain assertion|none|yes"),
                                                ("Did you go to the park?", f"past|affirmative|question|addressee|{N}|none|no")]),
 ("time-01", "B", "bare", "gemma3-4b", "P0", [("I can't go to the park, it's raining.", "unclear/mixed|negated|statement|speaker|plain assertion|none|yes")]),
]
DIMS = ["critical", "polarity", "speech_act", "agent", "certainty", "politeness", "added_content"]


def oid(text):
    return "o_" + hashlib.sha256(text.encode()).hexdigest()[:12]


def main():
    fx = ROOT / "tests/fixtures"; run = ROOT / "runs/fixture"
    fx.mkdir(parents=True, exist_ok=True); run.mkdir(parents=True, exist_ok=True)
    with (fx / "probes_fixture.jsonl").open("w") as fh:
        for f in FAM:
            fh.write(json.dumps({**f, "notes": "fixture"}) + "\n")
    uniq, expl, gold = {}, [], {}
    for fam, var, ch, model, prompt, outs in ROWS:
        req = f"r_{fam}_{var}_{ch}_{model}_{prompt}"
        for si, (text, g) in enumerate(outs):
            o = oid(text)
            uniq[o] = text
            vis = visible(fam, var, ch)
            expl.append(dict(request_id=req, output_id=o, run_id="fixture", model=model,
                             prompt_id=prompt, channel=ch, family_id=fam, variant=var,
                             input_text=vis, sample_idx=0,
                             suggestion_idx=si if prompt == "P2" else 0,
                             valid=bool(text.strip()), finish_reason="stop"))
            if g:
                gold[(text_key(text), fam, vis)] = dict(zip(DIMS, g.split("|")))
    (run / "config.json").write_text(json.dumps(
        {"run_id": "fixture", "items_path": "tests/fixtures/probes_fixture.jsonl"}))
    with (run / "unique_outputs.jsonl").open("w") as fh:
        for o, t in uniq.items():
            fh.write(json.dumps({"output_id": o, "text": t}) + "\n")
    with (run / "exploded.jsonl").open("w") as fh:
        for r in expl:
            fh.write(json.dumps(r) + "\n")
    with (fx / "fixture_gold.jsonl").open("w") as fh:
        for (o, fam, vis), g in gold.items():
            fh.write(json.dumps({"text_id": o, "family_id": fam, "input_text": vis, **g}) + "\n")
    print(f"{len(FAM)} families, {len(expl)} occurrences, {len(uniq)} unique outputs, "
          f"{len(gold)} gold units")


if __name__ == "__main__":
    main()
