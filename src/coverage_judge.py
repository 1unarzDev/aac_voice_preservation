"""Coverage judge (PLAN section 3). One call per (draft, pair [, extra dimension]); blind to arm, input, condition, other drafts and
to which variant is intended. Returns value on the pair dimension and event/role match against A and B."""
from __future__ import annotations
import hashlib
import coverage_lib as L

TPL = L.prompt_text("coverage_judge.txt")
PSHA = hashlib.sha256(TPL.encode()).hexdigest()
EV = {"type": "string", "enum": ["yes", "partly", "no"]}


def schema(dim, xdim=None):
    props = {"value": {"type": "string", "enum": L.OPTIONS[dim]}, "event_A": EV, "event_B": EV}
    if xdim:
        props["extra_value"] = {"type": "string", "enum": L.OPTIONS[xdim]}
    return L.schema_obj(props)


def build(draft, A, B, dim, xdim=None):
    xb = ""
    if xdim:
        xb = (f'- "extra_value": the option the DRAFT expresses for a second aspect, {xdim}. {L.defn(xdim)} '
              f'Options: {", ".join(L.OPTIONS[xdim])}.\n')
    return L.fill(TPL, A=A, B=B, draft=draft, dim=dim, question=L.defn(dim), options=", ".join(L.OPTIONS[dim]), extra_block=xb)


async def judge(chat, model, draft, A, B, dim, xdim=None, effort="low"):
    xdim = xdim if xdim and xdim != dim else None
    return await chat.one(model, build(draft, A, B, dim, xdim), temp=None, schema=schema(dim, xdim), effort=effort,
                          tag=f"judge|{PSHA[:8]}", max_tokens=600)
