"""Deterministic T/V register detector (lexicons fixed before outputs; see PLAN.md Sec. 4).
label(lang, text) -> 'T' | 'V' | 'none' | 'mixed' | 'ambig'  ('ambig' goes to the blind arbiter)."""
from __future__ import annotations
import re

W = lambda p: re.compile(r"(?<![\w'’])(?:%s)(?![\w])" % p, re.I | re.U)
W_CS = lambda p: re.compile(r"(?<![\w'’])(?:%s)(?![\w])" % p, re.U)  # case-sensitive

# German
DE_T = W(r"du|dich|dir|dein|deine|deinen|deinem|deiner|deines|bist|hast|kannst|willst|musst|sollst|wirst|darfst|brauchst|möchtest|könntest|würdest|solltest|hättest|gehst|kommst|siehst|machst")
DE_V_MID = re.compile(r"(?<=[\w,;:!?»“\"'’)] )(Sie|Ihnen|Ihr|Ihre|Ihren|Ihrem|Ihrer|Ihres)(?![\w])", re.U)
DE_V_INIT = re.compile(r"^\W*(Sie|Ihnen|Ihr|Ihre|Ihren|Ihrem|Ihrer|Ihres)(?![\w])", re.U)
# Spanish
ES_T = W(r"tú|tu|tus|ti|contigo|te|tienes|puedes|podrías|quieres|eres|estás|necesitas|debes|sabes|vas|haces|puedas|quieras|vienes|dime|dame|ven|trae|sé|ten|mira|oye|hazlo|ayúdame|llámame")
ES_V = W(r"usted|ustedes|le")
ES_V_WEAK = W(r"puede|podría|tiene|quiere|necesita|desea|tenga|traiga|venga|llame|espere|firme|pase|diga|tome|envíe|mande|ayude|hágame|dígame|permítame|vuelva|siéntese|acompáñeme")
# French
FR_T = re.compile(r"(?<![\w'’])(?:tu|toi|te|ton|ta|tes)(?![\w])|(?<![\w])t['’]\w", re.I | re.U)
FR_V = W(r"vous|votre|vos")


def label(lang: str, s: str) -> str:
    t = s.strip()
    if lang == "de":
        tt = bool(DE_T.search(t))
        vv = bool(DE_V_MID.search(t))
        init = bool(DE_V_INIT.search(t))
        if init and not vv:
            if tt:
                return "mixed"
            return "ambig"
        if tt and vv:
            return "mixed"
        return "T" if tt else "V" if vv else "none"
    if lang == "es":
        tt = bool(ES_T.search(t))
        vv = bool(re.search(r"(?<![\w])usted(?![\w])", t, re.I))
        # 'le' as clitic and weak 3sg verbs are ambiguous
        if tt and vv:
            return "mixed"
        if tt:
            return "T"
        if vv:
            return "V"
        if ES_V.search(t) or ES_V_WEAK.search(t):
            return "ambig"
        return "none"
    if lang == "fr":
        t = re.sub(r"rendez-vous", "rdv", t, flags=re.I)
        tt = bool(FR_T.search(t))
        vv = bool(FR_V.search(t))
        if tt and vv:
            return "mixed"
        return "T" if tt else "V" if vv else "none"
    raise ValueError(lang)
