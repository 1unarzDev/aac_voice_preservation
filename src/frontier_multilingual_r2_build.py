"""Round-2 request set. Frozen pilot items; adds EN comparator, plain_neg, legend-equalised arms, keyword-condition controls, sampled draws."""
from __future__ import annotations
import asyncio, json, re, sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_r2_lib import *  # noqa
import httpx

P0 = (ROOT / "prompts/P0.txt").read_text().strip()
LEG = (ROOT / "prompts/chip_legend.txt").read_text().strip()
LEG_X = LEG + "\n[FORMAL] address the listener formally; [INFORMAL] address the listener informally."
ADDED = "Write the sentence in {lang}."
CTX = {"de": ("Gespräch mit dem Arzt.", "Gespräch mit dem besten Freund."), "es": ("Hablando con el médico.", "Hablando con el mejor amigo."),
       "fr": ("Conversation avec le médecin.", "Conversation avec le meilleur ami.")}
PLAIN = {"de": ("formell", "informell"), "es": ("formal", "informal"), "fr": ("formel", "informel")}
NEGW = {"en": "not", "de": "nicht", "es": "no", "fr": "pas"}
LEX = {"de": r"nicht|kein\w*|nie|niemals|nichts|du|dich|dir|dein\w*|sie|ihnen|ihr\w*|bitte|euch|euer|ohne",
       "es": r"no|nunca|nada|sin|tu|tus|tú|usted|ustedes|te|ti|vos|su|sus|por favor|jamás|ningún\w*|ninguna",
       "fr": r"ne|pas|jamais|rien|n|tu|te|ton|ta|tes|toi|vous|votre|vos|s'il|plaît|plait|aucun\w*|sans"}
NOM = ("Translate this English keyword string for an AAC app into {lang}. Return ONLY a JSON object {{\"keywords\": \"...\"}}.\n"
       "Use only nouns and verbal nouns / nominalisations (for example a noun phrase naming the action and its object). Do NOT use any verb form: "
       "no infinitive, no imperative, no participle, no conjugated verb. No pronouns, no negation, no please, no formal/informal words, no added words.\nInput: {kw}")
SEP = ("Translate this English keyword string for an AAC app into German. Return ONLY a JSON object {{\"keywords\": \"...\"}}.\n"
       "Use the verb in the infinitive with a SEPARABLE prefix (like anrufen, mitbringen, ausschalten, einladen, anklopfen, weglassen) so that the infinitive "
       "differs from the formal imperative (anrufen vs. rufen Sie an). If no natural separable-prefix verb exists for this meaning, return {{\"keywords\": null}}. "
       "No pronouns, no negation, no please, no formal/informal words.\nInput: {kw}")
SEPPFX = re.compile(r"\b(an|auf|aus|ab|mit|ein|zu|weg|zurück|vor|hin|her|fest|los|nach|um|fort|bei)(rufen|bringen|schalten|laden|klopfen|lassen|treffen|schicken|geben|nehmen|machen|stellen|spielen|schneiden|schließen|kommen|sagen|senden|holen|legen|räumen|drehen|fahren|gehen|schreiben|sehen|bauen|reichen|stecken|sprechen)\w*", re.I)


def render(lang, kw_line, legend, ctx):
    t = P0
    if lang != "en":
        t = t.replace("Output only the sentence.", "Output only the sentence. " + ADDED.format(lang=LANGS[lang]))
    return t.replace("{legend}", legend).replace("{context}", f"Situation: {ctx}\n" if ctx else "").replace("{input}", kw_line)


def lexok(lang, kw):
    return not [x for x in re.findall(r"[\w']+", kw.lower()) if re.fullmatch(LEX[lang], x)]


async def main():
    tr = [r for r in jl(OUT / "translations.jsonl") if r["accepted"]]
    sem = asyncio.Semaphore(4)
    en_fam = {}
    for r in jl(OUT / "translations.jsonl"):
        en_fam.setdefault(r["family_id"], r)
    kw2 = {(r["lang"], r["family_id"]): r["kw2"] for r in jl(OUT / "r2_translator2_keywords.jsonl") if r["ok"]} if (OUT / "r2_translator2_keywords.jsonl").exists() else {}
    nom, sep = {}, {}
    async with httpx.AsyncClient() as c:
        async def one(r):
            if r["kind"] != "REG":
                return
            j = pj(await chat2(c, sem, "gpt-6.1-terra", NOM.format(lang=LANGS[r["lang"]], kw=r["bare"]), 300))
            kw = (j or {}).get("keywords") if isinstance(j, dict) else None
            if isinstance(kw, str) and lexok(r["lang"], kw):
                nom[(r["lang"], r["family_id"])] = kw
            if r["lang"] == "de":
                j = pj(await chat2(c, sem, "gpt-6.1-terra", SEP.format(kw=r["bare"]), 300))
                kw = (j or {}).get("keywords") if isinstance(j, dict) else None
                if isinstance(kw, str) and lexok("de", kw) and SEPPFX.search(kw):
                    sep[("de", r["family_id"])] = kw
        await asyncio.gather(*[one(r) for r in tr])
    reqs = []
    def add(lang, kind, fam, arm, variant, pset, prompt, temp=0.0, draw=0):
        reqs.append({"id": h(lang, kind, fam, arm, variant, pset, temp, draw)[:16], "lang": lang, "kind": kind, "family_id": fam, "arm": arm, "variant": variant,
                     "pset": pset, "temp": temp, "draw": draw, "prompt": prompt, "prompt_sha": h(prompt)[:12]})
    fams = {"POL": [], "REG": []}
    for r in jl(OUT / "translations.jsonl"):
        if r["lang"] == "de":
            fams[r["kind"]].append(r["family_id"])
    for r in tr:  # accepted target-language rows (pilot-frozen)
        lang, fam, kw, kind = r["lang"], r["family_id"], r["t"]["keywords"], r["kind"]
        if kind == "POL":
            add(lang, kind, fam, "bare", "AB", "L", render(lang, f"Keywords: {kw}", LEG, None))
            add(lang, kind, fam, "restored", "A", "L", render(lang, f"Keywords: [YES] {kw}", LEG, None))
            add(lang, kind, fam, "restored", "B", "L", render(lang, f"Keywords: [NOT] {kw}", LEG, None))
            add(lang, kind, fam, "plain_neg", "B", "L", render(lang, f"Keywords: {kw} {NEGW[lang]}", LEG, None))
            for d in range(5):
                add(lang, kind, fam, "bare_s", "AB", "L", render(lang, f"Keywords: {kw}", LEG, None), 0.7, d)
        else:
            add(lang, kind, fam, "bare", "-", "L", render(lang, f"Keywords: {kw}", LEG, None))
            add(lang, kind, fam, "chip_formal", "-", "L", render(lang, f"Keywords: [FORMAL] {kw}", LEG_X, None))
            add(lang, kind, fam, "chip_informal", "-", "L", render(lang, f"Keywords: [INFORMAL] {kw}", LEG_X, None))
            for tag, leg in (("", LEG), ("_x", LEG_X)):
                if tag:
                    add(lang, kind, fam, "bare_x", "-", "L", render(lang, f"Keywords: {kw}", leg, None))
                add(lang, kind, fam, "plain_formal" + tag, "-", "L", render(lang, f"Keywords: {kw} {PLAIN[lang][0]}", leg, None))
                add(lang, kind, fam, "plain_informal" + tag, "-", "L", render(lang, f"Keywords: {kw} {PLAIN[lang][1]}", leg, None))
                add(lang, kind, fam, "ctx_formal" + tag, "-", "L", render(lang, f"Keywords: {kw}", leg, CTX[lang][0]))
                add(lang, kind, fam, "ctx_informal" + tag, "-", "L", render(lang, f"Keywords: {kw}", leg, CTX[lang][1]))
            for d in range(5):
                add(lang, kind, fam, "bare_s", "-", "L", render(lang, f"Keywords: {kw}", LEG, None), 0.7, d)
            for tag, dd in (("bare_nom", nom), ("bare_sep", sep), ("bare_kw2", kw2)):
                if (lang, fam) in dd:
                    add(lang, kind, fam, tag, "-", "L", render(lang, f"Keywords: {dd[(lang, fam)]}", LEG, None))
    # English matched comparator: same families (hash order from translations), original English bare keywords
    seen = set()
    for fid, r in en_fam.items():
        kw, kind = r["bare"], r["kind"]
        if kind == "POL":
            add("en", kind, fid, "bare", "AB", "L", render("en", f"Keywords: {kw}", LEG, None))
            add("en", kind, fid, "restored", "A", "L", render("en", f"Keywords: [YES] {kw}", LEG, None))
            add("en", kind, fid, "restored", "B", "L", render("en", f"Keywords: [NOT] {kw}", LEG, None))
            add("en", kind, fid, "plain_neg", "B", "L", render("en", f"Keywords: {kw} not", LEG, None))
            for d in range(5):
                add("en", kind, fid, "bare_s", "AB", "L", render("en", f"Keywords: {kw}", LEG, None), 0.7, d)
        else:
            add("en", kind, fid, "bare", "-", "L", render("en", f"Keywords: {kw}", LEG, None))
            for d in range(5):
                add("en", kind, fid, "bare_s", "-", "L", render("en", f"Keywords: {kw}", LEG, None), 0.7, d)
    # P0-LL bare from the pilot request file
    for q in jl(RUN / "requests.jsonl"):
        if q["pset"] == "LL":
            add(q["lang"], q["kind"], q["family_id"], "bare", q["variant"], "LL", q["prompt"])
    # dedupe by id
    uniq = {q["id"]: q for q in reqs}
    reqs = list(uniq.values())
    jdump(RUN2 / "requests.jsonl", reqs)
    json.dump({"nominal": {f"{k[0]}|{k[1]}": v for k, v in nom.items()}, "sep_de": {f"{k[0]}|{k[1]}": v for k, v in sep.items()},
               "kw2": {f"{k[0]}|{k[1]}": v for k, v in kw2.items()}}, open(OUT / "r2_keyword_conditions.json", "w"), ensure_ascii=False, indent=1)
    json.dump({"P0_sha": h(P0)[:16], "legend_sha": h(LEG)[:16], "legend_x_sha": h(LEG_X)[:16]}, open(OUT / "r2_prompt_shas.json", "w"))
    print(len(reqs), collections.Counter((q["lang"], q["arm"]) for q in reqs))
    print("nom", len(nom), "sep", len(sep), "kw2", len(kw2))

asyncio.run(main())
