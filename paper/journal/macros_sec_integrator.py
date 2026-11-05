"""Integrator-pass macros (pass 2): arbiter-check sensitivity to excluded codings and coder dependence.
Reads analysis/arbiter_check/items.csv (read-only). Item-level bootstrap (items are the cluster)."""
import csv, random


def register(ctx):
    put, A = ctx["put"], ctx["A"]

    def arb_sens():
        src = "analysis/arbiter_check/items.csv"
        rows = [r for r in csv.DictReader(open(A / "arbiter_check" / "items.csv")) if r["source"] == "arbiter"]
        per = []  # per item: list of (coder, label)
        for r in rows:
            cl = []
            for tok in r["coder_labels"].split("|"):
                c, _, l = tok.partition(":")
                cl.append((c, l.strip()))
            per.append((r["arbiter_label"], cl))
        tot = sum(len(cl) for _, cl in per)
        lab = [(a, c, l) for a, cl in per for c, l in cl if l]
        k = sum(1 for a, c, l in lab if l == a)
        put("p19SensTotal", tot, src, "int"); put("p19SensLabelled", len(lab), src, "int")
        put("p19SensUnsure", (tot - len(lab)) / tot, src)
        put("p19SensLowerBound", k / tot, src)  # unsure counted as disagreement
        # leave-one-coder-out
        coders = sorted({c for _, cl in per for c, _ in cl})
        loo = []
        for x in coders:
            kk = [(a, l) for a, c, l in lab if c != x]
            loo.append(sum(1 for a, l in kk if l == a) / len(kk))
        put("p19SensLooMin", min(loo), src); put("p19SensLooMax", max(loo), src)
        # per-coder range (coders with >=5 labelled codings)
        pc = []
        for x in coders:
            kk = [(a, l) for a, c, l in lab if c == x]
            if len(kk) >= 5:
                pc.append(sum(1 for a, l in kk if l == a) / len(kk))
        put("p19SensCoderMin", min(pc), src); put("p19SensCoderMax", max(pc), src); put("p19SensCoderN", len(pc), src, "int")
        # item-clustered bootstrap
        rnd = random.Random(20261104)
        bs = []
        for _ in range(5000):
            s = [per[rnd.randrange(len(per))] for _ in per]
            n = kk = 0
            for a, cl in s:
                for c, l in cl:
                    if l:
                        n += 1; kk += (l == a)
            if n: bs.append(kk / n)
        bs.sort()
        put("p19SensBootLo", bs[int(.025 * len(bs))], src); put("p19SensBootHi", bs[int(.975 * len(bs))], src)
        # items with at least one label
        put("p19SensItemsAnyLabel", sum(1 for a, cl in per if any(l for _, l in cl)), src, "int")
        put("p19SensCoderPairs", len({tuple(sorted(c for c, _ in cl)) for a, cl in per}), src, "int")
    return [arb_sens]
