"""Stage 0: select items by declared hash rule, forward-translate (terra), back-translate (sol, blind), check."""
from __future__ import annotations
import asyncio, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from frontier_multilingual_lib import *  # noqa
import httpx

N = 20
items = jl(ROOT / "data/items/hw.jsonl")
YOU = re.compile(r"\b(you|your|yours)\b", re.I)
NEG = re.compile(r"\b(not|no|never|n't|don't|cannot|nothing|nobody|none)\b|n't", re.I)
PLS = re.compile(r"\bplease\b", re.I)


def pol_ok(f):
    if f["dimension"] != "polarity":
        return False
    A, B = f["variants"]["A"]["source"], f["variants"]["B"]["source"]
    return not YOU.search(A + " " + B) and not NEG.search(f["bare"]) and not PLS.search(f["bare"]) \
        and f["variants"]["A"]["critical_value"] == "affirmative" and f["variants"]["B"]["critical_value"] == "negated"


def reg_ok(f):
    if f["dimension"] not in ("speech_act", "politeness"):
        return False
    A = f["variants"]["A"]
    return bool(YOU.search(A["source"])) and not NEG.search(f["bare"]) and not PLS.search(f["bare"])


def order(salt, fs):
    return sorted(fs, key=lambda f: h(salt + "|" + f["family_id"]))


pol = order("ml1", [f for f in items if pol_ok(f)])[:N]
reg = order("ml1reg", [f for f in items if reg_ok(f)])[:N]
sel = [{"kind": "POL", **{k: f[k] for k in ("family_id", "bare")}, "A": f["variants"]["A"]["source"], "B": f["variants"]["B"]["source"]} for f in pol] + \
      [{"kind": "REG", "family_id": f["family_id"], "bare": f["bare"], "A": f["variants"]["A"]["source"], "B": None} for f in reg]
print("eligible", sum(map(pol_ok, items)), sum(map(reg_ok, items)))

FWD = ("Translate into {lang}. Return ONLY a JSON object with keys {keys}.\n"
       "- \"A\" and \"B\" are sentences: translate faithfully, preserving polarity (affirmative stays affirmative, negated stays negated).\n"
       "- \"keywords\" is a short English keyword string for an AAC app: translate it into {lang} as bare lemma/infinitive forms, "
       "with NO negation word and NO register-marking word (no du/Sie/tu/vous/tu/usted, no please), no added words; keep any "
       "listener-directed verb in the infinitive.\n"
       "Input: {inp}")
BACK = ("Translate this {lang} text into English, literally. You see no original. Return ONLY a JSON object with the same keys.\n{inp}")
POLQ = ("Is the following English sentence negated (contains a negation of the main statement) or affirmative? "
        "Answer with one word: negated or affirmative.\nSentence: {s}")


def pj(t):
    if not t:
        return None
    m = re.search(r"\{.*\}", t, re.S)
    try:
        return json.loads(m.group(0))
    except Exception:  # noqa: BLE001
        return None


LEX = {"de": r"nicht|kein\w*|nie|niemals|nichts|du|dich|dir|dein\w*|sie|ihnen|ihr\w*|bitte|euch|euer|ohne",
       "es": r"no|nunca|nada|sin|tu|tus|tú|usted|ustedes|te|ti|vos|su|sus|por favor|jamás|ningún\w*|ninguna",
       "fr": r"ne|pas|jamais|rien|n|tu|te|ton|ta|tes|toi|vous|votre|vos|s'il|plaît|plait|aucun\w*|sans"}


def lex_hit(lang, kw):
    toks = re.findall(r"[\w']+", kw.lower())
    return [t for t in toks if re.fullmatch(LEX[lang], t)]


def overlap(en, back):
    stop = {"to", "a", "the", "of", "and", "be"}
    e = [t for t in re.findall(r"[a-z]+", en.lower()) if t not in stop]
    b = [t for t in re.findall(r"[a-z]+", back.lower()) if t not in stop]
    if not e:
        return 0.0
    hit = sum(any(x[:3] == y[:3] for y in b) for x in e)
    return hit / len(e)


async def main():
    sem = asyncio.Semaphore(4)
    async with httpx.AsyncClient() as c:
        async def one(s, lang):
            keys = '"A", "B", "keywords"' if s["B"] else '"A", "keywords"'
            inp = json.dumps({k: s[k] if k != "keywords" else s["bare"] for k in (["A", "B"] if s["B"] else ["A"])} | {"keywords": s["bare"]}, ensure_ascii=False)
            fw = await chat(c, sem, "gpt-6.1-terra", FWD.format(lang=LANGS[lang], keys=keys, inp=inp), 1200)
            t = pj(fw)
            r = {"lang": lang, **{k: s[k] for k in ("kind", "family_id", "bare", "A", "B")}, "t": t}
            if not t:
                return r
            bk = {k: t[k] for k in t if k in ("A", "B", "keywords")}
            bt = pj(await chat(c, sem, "gpt-6.1-sol", BACK.format(lang=LANGS[lang], inp=json.dumps(bk, ensure_ascii=False)), 3000))
            r["back"] = bt
            if bt and s["B"]:
                r["back_pol"] = {}
                for k in ("A", "B"):
                    x = (await chat(c, sem, "gpt-6.1-sol", POLQ.format(s=bt.get(k, "")), 2000) or "").strip().lower()
                    r["back_pol"][k] = "negated" if x.startswith("neg") else "affirmative" if x.startswith("aff") else "?"
            return r
        res = await asyncio.gather(*[one(s, l) for s in sel for l in LANGS])
    rows = []
    for r in res:
        why = []
        t, bt = r.get("t"), r.get("back")
        if not t or not bt:
            why.append("translation_failed")
        else:
            if r["kind"] == "POL":
                if r["back_pol"].get("A") != "affirmative" or r["back_pol"].get("B") != "negated":
                    why.append("polarity_not_preserved")
            if lex_hit(r["lang"], t["keywords"]):
                why.append("kw_lexicon:" + ",".join(lex_hit(r["lang"], t["keywords"])))
            ov = overlap(r["bare"], bt.get("keywords", ""))
            r["kw_overlap"] = ov
            if ov < 0.5:
                why.append("kw_overlap<0.5")
        r["accepted"] = not why
        r["drop_reasons"] = why
        rows.append(r)
    jdump(OUT / "translations.jsonl", rows)
    import collections
    tab = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        tab[(r["lang"], r["kind"])][0] += 1
        tab[(r["lang"], r["kind"])][1] += r["accepted"]
    for k, v in sorted(tab.items()):
        print(k, v)

asyncio.run(main())
