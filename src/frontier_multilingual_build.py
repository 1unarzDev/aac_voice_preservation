"""Build the pilot request set (P0-L and P0-LL prompts, all arms) from accepted translations. No generation here except template translation."""
from __future__ import annotations
import asyncio, json, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
import httpx

P0 = (ROOT / "prompts/P0.txt").read_text().strip()
LEG = (ROOT / "prompts/chip_legend.txt").read_text().strip()
LEG_X = LEG + "\n[FORMAL] address the listener formally; [INFORMAL] address the listener informally."
ADDED = "Write the sentence in {lang}."
CTX = {"de": ("Gespräch mit dem Arzt.", "Gespräch mit dem besten Freund."),
       "es": ("Hablando con el médico.", "Hablando con el mejor amigo."),
       "fr": ("Conversation avec le médecin.", "Conversation avec le meilleur ami.")}
PLAIN = {"de": ("formell", "informell"), "es": ("formal", "informal"), "fr": ("formel", "informel")}
KW = {"de": "Schlüsselwörter", "es": "Palabras clave", "fr": "Mots-clés"}
SIT = {"de": "Situation", "es": "Situación", "fr": "Situation"}
TT = ("Translate the following instructions for an app component into {lang}. Keep the placeholders {{legend}}, {{context}}, {{input}} "
      "exactly as written on their own, and keep every bracketed chip token (like [NOT], [YES], [?], [FORMAL]) exactly unchanged. "
      "Also state that the sentence must be written in {lang}. Output only the translation.\n\n{txt}")


def render_en(lang, kw_line, legend, ctx):
    t = P0.replace("Output only the sentence.", "Output only the sentence. " + ADDED.format(lang=LANGS[lang]))
    return t.replace("{legend}", legend).replace("{context}", f"Situation: {ctx}\n" if ctx else "").replace("{input}", kw_line)


async def main():
    tr = [r for r in jl(OUT / "translations.jsonl") if r["accepted"]]
    sem = asyncio.Semaphore(3)
    tmpl = {}
    async with httpx.AsyncClient() as c:
        for lang in LANGS:
            for tag, leg in (("base", LEG), ("x", LEG_X)):
                txt = P0.replace("{legend}", "{legend}") + "\n\nLEGEND:\n" + leg
                out = await chat(c, sem, "gpt-6.1-terra", TT.format(lang=LANGS[lang], txt=txt), 2500)
                # split translated template / legend
                tmpl[(lang, tag)] = out
    reqs = []
    def add(lang, kind, fam, arm, variant, pset, prompt):
        reqs.append({"id": h(lang, kind, fam, arm, variant, pset)[:16], "lang": lang, "kind": kind, "family_id": fam, "arm": arm,
                     "variant": variant, "pset": pset, "prompt": prompt, "prompt_sha": h(prompt)[:12]})
    for r in tr:
        lang, fam, kw = r["lang"], r["family_id"], r["t"]["keywords"]
        if r["kind"] == "POL":
            add(lang, "POL", fam, "bare", "AB", "L", render_en(lang, f"Keywords: {kw}", LEG, None))
            add(lang, "POL", fam, "restored", "A", "L", render_en(lang, f"Keywords: [YES] {kw}", LEG, None))
            add(lang, "POL", fam, "restored", "B", "L", render_en(lang, f"Keywords: [NOT] {kw}", LEG, None))
        else:
            add(lang, "REG", fam, "bare", "-", "L", render_en(lang, f"Keywords: {kw}", LEG, None))
            add(lang, "REG", fam, "chip_formal", "-", "L", render_en(lang, f"Keywords: [FORMAL] {kw}", LEG_X, None))
            add(lang, "REG", fam, "chip_informal", "-", "L", render_en(lang, f"Keywords: [INFORMAL] {kw}", LEG_X, None))
            add(lang, "REG", fam, "plain_formal", "-", "L", render_en(lang, f"Keywords: {kw} {PLAIN[lang][0]}", LEG, None))
            add(lang, "REG", fam, "plain_informal", "-", "L", render_en(lang, f"Keywords: {kw} {PLAIN[lang][1]}", LEG, None))
            add(lang, "REG", fam, "ctx_formal", "-", "L", render_en(lang, f"Keywords: {kw}", LEG, CTX[lang][0]))
            add(lang, "REG", fam, "ctx_informal", "-", "L", render_en(lang, f"Keywords: {kw}", LEG, CTX[lang][1]))
        # LL: fully translated template, bare
        tl = tmpl[(lang, "base")]
        if tl:
            blocks = [b.strip() for b in tl.strip().split("\n\n") if b.strip()]
            body = blocks[0] + "\n\n" + blocks[-1] + "\n\n" + f"{KW[lang]}: {kw}"
            add(lang, r["kind"], fam, "bare", "AB" if r["kind"] == "POL" else "-", "LL", body)
    jdump(RUN / "requests.jsonl", reqs)
    json.dump({f"{l}|{t}": v for (l, t), v in tmpl.items()}, open(OUT / "translated_templates.json", "w"), ensure_ascii=False, indent=1)
    json.dump({"P0_sha": h(P0)[:16], "legend_sha": h(LEG)[:16], "legend_x_sha": h(LEG_X)[:16], "added_line": ADDED}, open(OUT / "prompt_shas.json", "w"), indent=1)
    import collections
    print(len(reqs), collections.Counter((q["lang"], q["pset"]) for q in reqs))
    print(tmpl[("de", "base")])

asyncio.run(main())
