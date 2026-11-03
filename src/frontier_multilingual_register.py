"""v2 (single allowed revision, see DEVIATIONS.md; v1 kept in frontier_multilingual_register_v1.py).
Deterministic T/V register detector (lexicons fixed before outputs; see PLAN.md Sec. 4).
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


# ---- v2 additions: pronoun-less imperatives / 2sg morphology of the stimulus verbs (lexicon from the fixed REG keyword set)
_LEAD = r"^\W*(?:(?:bitte|por favor|s['’]il (?:te|vous) pla[iî]t)[\s,]*)?"
DE_T_IMP = re.compile(_LEAD + r"(?:bring|bringe|schalte|stell|stelle|lass|lasse|schick|schicke|schließ|schließe|schneid|schneide|ruf|rufe|lad|lade|klopf|klopfe|spiel|triff|nimm|sag|komm|gib|hilf|warte|mach|mache)(?![\w])", re.I | re.U)
ES_T_IMP = re.compile(_LEAD + r"¿?(?:baja|apaga|cierra|corta|deja|envía|llama|lleva|trae|toca|invita|encuéntrate|déjame|tráeme|llámame|córtame|bájame|apágame|envíame|llévame|invítame|dame|dime|ven|ayúdame)(?![\w])", re.I | re.U)
ES_T_2SG = W(r"tocas|traes|apagas|bajas|dejas|llamas|llevas|cortas|envías|cierras|invitas|encuentras|traigas|bajes|apagues|cierres|cortes|dejes|envíes|llames|lleves|invites|toques")
ES_V_IMP = re.compile(_LEAD + r"¿?(?:baje|apague|cierre|corte|deje|envíe|llame|lleve|traiga|toque|invite|encuéntrese|siéntese|tráigame|déjeme|bájeme|apágueme|llámeme|córteme|envíeme|lléveme|invíteme|dígame|ayúdeme|venga|pase|espere)(?![\w])", re.I | re.U)
ES_V_Q = re.compile(r"¿\s*(?:por favor,?\s*)?(?:me\s+)?(?:puede|pueden|podría|podrían|tiene|desea|quiere|le gustaría)(?![\w])", re.I | re.U)
FR_V_IMP = re.compile(_LEAD + r"(?:veuillez|apportez|envoyez|laissez|fermez|éteignez|baissez|coupez|frappez|appelez|invitez|jouez|retrouvez|pouvez|voulez|donnez)(?![\w])", re.I | re.U)
FR_T_IMP = re.compile(_LEAD + r"(?:apporte|envoie|laisse|ferme|éteins|baisse|coupe|frappe|appelle|invite|joue|retrouve|donne|viens|peux|veux)(?![\w])", re.I | re.U)


def label(lang: str, s: str) -> str:
    t = s.strip()
    base = _label_v1(lang, t)
    if base in ("T", "V", "mixed"):
        return base
    # base is 'none' or 'ambig': look for pronoun-less address forms
    if lang == "de":
        return "T" if DE_T_IMP.search(t) else base
    if lang == "es":
        tt = bool(ES_T_IMP.search(t) or ES_T_2SG.search(t))
        vv = bool(ES_V_IMP.search(t) or ES_V_Q.search(t))
        if tt and vv:
            return "mixed"
        return "T" if tt else "V" if vv else base
    if lang == "fr":
        tt = bool(FR_T_IMP.search(t))
        vv = bool(FR_V_IMP.search(t))
        if tt and vv:
            return "mixed"
        return "T" if tt else "V" if vv else base
    return base


def _label_v1(lang: str, s: str) -> str:
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
