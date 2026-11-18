"""Fresh seeded-fault set (problem #10 part A). Plan: analysis/fresh_validation/PLAN.md (frozen before any run).

  python src/fresh_faults.py enumerate   # sites.json (AST walk; no pick yet)
  python src/fresh_faults.py pick        # faults_table.json (FB01-FB40 + R01-R10) from sites + hand-written F6/F7 sites
  python src/fresh_faults.py validate    # apply + py_compile + import ONLY (no pytest); replaces failed primaries by reserves (logged)
  python src/fresh_faults.py freeze      # FREEZE.json (table sha, tests/ sha, HEAD, columns)
  python src/fresh_faults.py run [--jobs 6]   # one sweep via src/seeded_faults.py machinery; refuses if tests/ hash differs

Built from the source of the target modules and the plan only (tests/ and survivor sections not read).
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import random
import subprocess
import sys
from pathlib import Path

REAL = Path(__file__).resolve().parents[1]
OUT = REAL / "analysis" / "fresh_validation"
SEED = 20261118
MODS = {"LS": ["src/score_listener_study.py"], "RA": ["src/score_repair_audit.py"], "OI": ["src/score_oracle_indep.py"],
        "MA": ["src/make_assignments.py"], "ML": ["src/make_listener_study.py"], "MF": ["src/make_frontier_parts.py"],
        "GD": ["src/guard_baseline.py"], "AN": ["src/analyze.py", "src/arbiter_tool.py"]}
MOD_ORDER = ["LS", "RA", "OI", "MA", "ML", "MF", "GD", "AN"]
# type x module quota (rows sum 5; columns sum to the plan's 6,5,4,5,5,5,4,6)
QUOTA = {"F1": dict(LS=1, RA=1, OI=1, MF=1, AN=1), "F2": dict(LS=1, OI=1, MA=1, GD=1, AN=1),
         "F3": dict(LS=1, RA=1, ML=1, MF=1, AN=1), "F4": dict(LS=1, RA=1, OI=1, GD=1, AN=1),
         "F5": dict(RA=1, MA=1, ML=1, MF=1, AN=1), "F6": dict(MA=2, ML=2, MF=1),
         "F7": dict(LS=1, RA=1, OI=1, MF=1, GD=1), "F8": dict(LS=1, MA=1, ML=1, GD=1, AN=1)}
TYPES = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"]
HAND = {"F6", "F7"}


# ------------------------------------------------------------------ enumerate
def _seg(lb, n):
    return lb[n.col_offset:n.end_col_offset]


def _sites_for_file(rel):
    text = (REAL / rel).read_text(encoding="utf-8")
    lines = text.split("\n")
    tree = ast.parse(text)
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and n.body and isinstance(n.body[0], ast.Expr) \
                and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str):
            doc.add(id(n.body[0].value))
    parents = {}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p):
            parents[id(c)] = p
    out = []

    def add(t, node, new_bytes_fn, desc):
        if node.lineno != node.end_lineno:
            return
        lb = lines[node.lineno - 1].encode("utf-8")
        try:
            new_lb = new_bytes_fn(lb)
        except Exception:
            return
        if new_lb is None or new_lb == lb:
            return
        orig, new = lb.decode("utf-8"), new_lb.decode("utf-8")
        if text.count(orig) != 1 or not orig.strip() or orig.strip().startswith("#"):
            return
        out.append(dict(type=t, file=rel, line=node.lineno, original=orig, mutated=new, desc=desc))

    def sub(node_a, node_b, repl_fn):  # replace bytes between spans
        pass

    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in (ast.Lt, ast.LtE, ast.Gt, ast.GtE):
            op = type(n.ops[0])
            tok, rep = {ast.Lt: (b" < ", b" <= "), ast.LtE: (b" <= ", b" < "), ast.Gt: (b" > ", b" >= "), ast.GtE: (b" >= ", b" > ")}[op]

            def f(lb, n=n, tok=tok, rep=rep):
                a, b = n.left.end_col_offset, n.comparators[0].col_offset
                mid = lb[a:b]
                if mid != tok:
                    return None
                return lb[:a] + rep + lb[b:]
            add("F1", n, f, f"comparison edge {tok.decode().strip()} -> {rep.decode().strip()}")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "range" and len(n.args) == 1 and n.lineno == n.end_lineno:
            a = n.args[0]

            def f(lb, a=a):
                return lb[:a.end_col_offset] + b" - 1" + lb[a.end_col_offset:]
            add("F1", n, f, "range(n) -> range(n - 1)")
        if isinstance(n, ast.Slice) and n.upper is not None and n.upper.lineno == n.upper.end_lineno:
            u = n.upper

            def f(lb, u=u):
                return lb[:u.end_col_offset] + b" - 1" + lb[u.end_col_offset:]
            add("F1", u, f, "slice end -1")
        # F2 constants
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool) and id(n) not in doc:
            par = parents.get(id(n))
            if isinstance(par, (ast.Subscript, ast.Slice, ast.JoinedStr, ast.FormattedValue)) or n.value in (0, 1):
                pass
            else:
                v = n.value
                if v == 1.96:
                    nv, d = "1.64", "z 1.96 -> 1.64"
                elif isinstance(v, int):
                    nv, d = str(v + 1), f"constant {v} -> {v + 1}"
                else:
                    nv, d = repr(v * 2), f"constant {v} -> {v * 2}"

                def f(lb, n=n, nv=nv):
                    return lb[:n.col_offset] + nv.encode() + lb[n.end_col_offset:]
                add("F2", n, f, d)
        if isinstance(n, ast.keyword) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, bool) and n.value.lineno == n.value.end_lineno:
            v = n.value

            def f(lb, v=v):
                return lb[:v.col_offset] + (b"False" if v.value else b"True") + lb[v.end_col_offset:]
            add("F2", v, f, f"default/flag {n.arg}={v.value} flipped")
        # F3 operands
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub) and isinstance(n.left, (ast.Name, ast.Attribute, ast.Subscript)) \
                and isinstance(n.right, (ast.Name, ast.Attribute, ast.Subscript)):
            def f(lb, n=n):
                L, R = _seg(lb, n.left), _seg(lb, n.right)
                return lb[:n.col_offset] + R + lb[n.left.end_col_offset:n.right.col_offset] + L + lb[n.end_col_offset:]
            add("F3", n, f, "operands of a difference swapped")
        if isinstance(n, ast.Call) and len(n.args) >= 2 and all(isinstance(a, (ast.Name, ast.Attribute)) for a in n.args[:2]) \
                and not (isinstance(n.func, ast.Name) and n.func.id in ("isinstance", "print", "min", "max", "sum", "zip", "range")):
            a0, a1 = n.args[0], n.args[1]

            def f(lb, a0=a0, a1=a1):
                return lb[:a0.col_offset] + _seg(lb, a1) + lb[a0.end_col_offset:a1.col_offset] + _seg(lb, a0) + lb[a1.end_col_offset:]
            add("F3", n, f, "first two positional arguments swapped")
        # F4 aggregation
        if isinstance(n, ast.Attribute) and n.attr in ("mean", "sum", "median", "max", "min") and isinstance(parents.get(id(n)), ast.Call):
            m = {"mean": "median", "median": "mean", "sum": "max", "max": "sum", "min": "max"}[n.attr]

            def f(lb, n=n, m=m):
                s = lb[n.end_col_offset - len(n.attr):n.end_col_offset]
                if s != n.attr.encode():
                    return None
                return lb[:n.end_col_offset - len(n.attr)] + m.encode() + lb[n.end_col_offset:]
            add("F4", n, f, f".{n.attr}() -> .{m}()")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("round", "sum", "mean", "float", "int") and n.func.lineno == n.func.end_lineno:
            m = {"round": "int", "sum": "max", "mean": "max", "float": "int", "int": "round"}[n.func.id]

            def f(lb, n=n, m=m):
                return lb[:n.func.col_offset] + m.encode() + lb[n.func.end_col_offset:]
            add("F4", n, f, f"{n.func.id}() -> {m}()")
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            def f(lb, n=n):
                a, b = n.left.end_col_offset, n.right.col_offset
                mid = lb[a:b]
                if mid.strip() != b"/":
                    return None
                return lb[:a] + mid.replace(b"/", b"//") + lb[b:]
            add("F4", n, f, "true division -> floor division")
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult) and isinstance(n.right, ast.Constant) and n.right.value == 100:
            def f(lb, n=n):
                return lb[:n.left.end_col_offset] + lb[n.end_col_offset:]
            add("F4", n, f, "percent x100 dropped")
        if isinstance(n, ast.keyword) and n.arg == "ddof" and isinstance(n.value, ast.Constant):
            v = n.value

            def f(lb, v=v):
                return lb[:v.col_offset] + str(1 - v.value).encode() + lb[v.end_col_offset:]
            add("F4", v, f, "ddof flipped")
        # F5 identity/key
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("drop_duplicates", "groupby", "merge", "sort_values"):
            cand = n.args[0] if n.args else None
            if isinstance(cand, ast.List) and len(cand.elts) >= 2:
                last, prev = cand.elts[-1], cand.elts[-2]

                def f(lb, last=last, prev=prev):
                    return lb[:prev.end_col_offset] + lb[last.end_col_offset:]
                add("F5", n, f, f"{n.func.attr}: last key column dropped")
            for kw in n.keywords:
                if kw.arg == "how" and isinstance(kw.value, ast.Constant) and kw.value.value in ("inner", "left"):
                    v = kw.value

                    def f(lb, v=v):
                        nv = b'"left"' if v.value == "inner" else b'"inner"'
                        return lb[:v.col_offset] + nv + lb[v.end_col_offset:]
                    add("F5", v, f, "merge how inner<->left")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "set" and len(n.args) == 1 and isinstance(n.args[0], (ast.Name, ast.Attribute, ast.ListComp, ast.GeneratorExp, ast.Call)):
            pass
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("sorted",) and len(n.args) == 1 \
                and isinstance(n.args[0], ast.Call) and isinstance(n.args[0].func, ast.Name) and n.args[0].func.id == "set":
            inner = n.args[0]

            def f(lb, n=n, inner=inner):
                return lb[:n.col_offset] + b"list(" + lb[inner.args[0].col_offset:inner.args[0].end_col_offset] + b")" + lb[n.end_col_offset:]
            add("F5", n, f, "sorted(set(x)) -> list(x): repeats kept / dedupe lost")
        # F8 normalisation
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("strip", "lower", "casefold") and not n.args:
            def f(lb, n=n):
                a = n.func.value.end_col_offset
                return lb[:a] + lb[n.end_col_offset:]
            add("F8", n, f, f".{n.func.attr}() dropped")
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in ("same", "different", "NFKC", "NFC", "A", "B") and id(n) not in doc:
            nv = {"same": "different", "different": "same", "NFKC": "NFC", "NFC": "NFKC", "A": "B", "B": "A"}[n.value]

            def f(lb, n=n, nv=nv):
                s = lb[n.col_offset:n.end_col_offset]
                q = s[:1]
                return lb[:n.col_offset] + q + nv.encode() + q + lb[n.end_col_offset:]
            add("F8", n, f, f"label/form map '{n.value}' -> '{nv}'")
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub):
            def f(lb, n=n):
                a, b = n.left.end_col_offset, n.right.col_offset
                mid = lb[a:b]
                if mid.strip() != b"-":
                    return None
                return lb[:a] + mid.replace(b"-", b"+") + lb[b:]
            add("F8", n, f, "sign flip of a difference (- -> +)")
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub) and isinstance(n.operand, (ast.Name, ast.Attribute, ast.Call)):
            def f(lb, n=n):
                return lb[:n.col_offset] + lb[n.operand.col_offset:]
            add("F8", n, f, "unary minus dropped")
    return out


def old_exclusions():
    spec = importlib.util.spec_from_file_location("seeded_faults_old", REAL / "src" / "seeded_faults.py")
    m = importlib.util.module_from_spec(spec)
    sys.argv = [sys.argv[0]]
    spec.loader.exec_module(m)
    ex = []
    for mu in m.MUTATIONS:
        for find, _ in mu["pairs"]:
            ex.append((mu["file"], find))
    return ex


def enumerate_sites():
    ex = old_exclusions()
    sites = []
    for mod in MOD_ORDER:
        for rel in MODS[mod]:
            for s in _sites_for_file(rel):
                if any(f == rel and (find in s["original"] or s["original"].strip() in find) for f, find in ex):
                    continue
                s["module"] = mod
                sites.append(s)
    for i, s in enumerate(sites):
        s["site_index"] = i
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sites.json").write_text(json.dumps(sites, indent=1))
    from collections import Counter
    print(len(sites), "sites;", dict(Counter((s["module"], s["type"]) for s in sites)))


# ------------------------------------------------------------------ pick
def pick():
    sites = json.loads((OUT / "sites.json").read_text())
    hand = json.loads((OUT / "hand_sites.json").read_text())   # written by hand from module specs (F6/F7)
    for h in hand:
        h.setdefault("site_index", -1)
    table, reserve_pool, moved = [], {}, {}
    used = set()
    for t in TYPES:
        for mod in MOD_ORDER:
            q = QUOTA[t].get(mod, 0)
            pool = [s for s in (hand if t in HAND else sites) if s["type"] == t and s["module"] == mod]
            if t not in HAND:
                random.Random(f"{SEED}|fresh|{t}|{mod}").shuffle(pool)
            pool = [s for s in pool if (s["file"], s["line"]) not in used]
            reserve_pool[(t, mod)] = pool[q:]
            for s in pool[:q]:
                table.append(dict(s, moved_from=None))
                used.add((s["file"], s["line"]))
            # shortfall: move to next module in order with sites of that type
            short = q - len(pool[:q])
            k = MOD_ORDER.index(mod)
            while short > 0:
                k = (k + 1) % len(MOD_ORDER)
                if MOD_ORDER[k] == mod:
                    break
                alt = [s for s in (hand if t in HAND else sites) if s["type"] == t and s["module"] == MOD_ORDER[k] and (s["file"], s["line"]) not in used]
                random.Random(f"{SEED}|fresh|{t}|{MOD_ORDER[k]}").shuffle(alt) if t not in HAND else None
                for s in alt[:short]:
                    table.append(dict(s, moved_from=mod))
                    used.add((s["file"], s["line"]))
                    short -= 1
    # reserve R01-R10: cycle types, first unused from per-(type,module) reserve pools in module order
    res = []
    i = 0
    while len(res) < 10 and i < 200:
        t = TYPES[i % 8]
        mod_cands = [m for m in MOD_ORDER if reserve_pool.get((t, m))]
        if mod_cands:
            m = mod_cands[(i // 8) % len(mod_cands)]
            s = reserve_pool[(t, m)].pop(0)
            if (s["file"], s["line"]) not in used:
                res.append(dict(s, moved_from=None))
                used.add((s["file"], s["line"]))
        i += 1
    for j, s in enumerate(table, 1):
        s["id"] = f"FB{j:02d}"
    for j, s in enumerate(res, 1):
        s["id"] = f"R{j:02d}"
    (OUT / "faults_table.json").write_text(json.dumps({"primary": table, "reserve": res, "swaps": []}, indent=1))
    from collections import Counter
    print(len(table), "primary;", len(res), "reserve;", dict(Counter(s["type"] for s in table)), dict(Counter(s["module"] for s in table)))


# ------------------------------------------------------------------ table -> seeded_faults format
def load_table():
    d = json.loads((OUT / "faults_table.json").read_text())
    return d


def as_mutations(rows):
    return [dict(id=r["id"], cls=r["type"], file=r["file"], desc=r["desc"], pairs=[[r["original"], r["mutated"]]]) for r in rows]


def _sf():
    spec = importlib.util.spec_from_file_location("seeded_faults_new", REAL / "src" / "seeded_faults.py")
    m = importlib.util.module_from_spec(spec)
    argv = sys.argv
    sys.argv = [argv[0]]
    spec.loader.exec_module(m)
    sys.argv = argv
    m.SF = REAL / "tmp" / "fv"
    m.DEPS = m.SF / "_deps"
    m.OUT = OUT
    m.PREFIX = "bugs_"
    return m


def validate():
    d = load_table()
    sf = _sf()
    sf.SF.mkdir(parents=True, exist_ok=True)
    reserve = list(d["reserve"])
    new_primary, swaps = [], list(d.get("swaps", []))
    import shutil

    def ok(r):
        mut = as_mutations([r])[0]
        try:
            wd = sf.build_workdir("V_" + r["id"], mut)
        except Exception as e:  # noqa
            return False, f"apply/compile: {str(e)[:120]}"
        try:
            mod = Path(r["file"]).stem
            p = subprocess.run([sf.PY, "-c", f"import sys;sys.path.insert(0,'src');import {mod}"], cwd=wd, capture_output=True, text=True, timeout=300)
            shutil.rmtree(wd, ignore_errors=True)
            if p.returncode != 0:
                return False, "import: " + p.stderr[-150:]
            return True, ""
        except Exception as e:  # noqa
            shutil.rmtree(wd, ignore_errors=True)
            return False, f"import-timeout {e}"
    for r in d["primary"]:
        good, why = ok(r)
        if good:
            new_primary.append(r)
            continue
        cand = [x for x in reserve if x["type"] == r["type"]] or [x for x in reserve if x["module"] == r["module"]] or reserve
        rep = None
        while cand:
            c = cand.pop(0)
            reserve.remove(c)
            g2, _ = ok(c)
            if g2:
                rep = c
                break
        if rep is None:
            print("NO REPLACEMENT for", r["id"], why)
            sys.exit(2)
        swaps.append({"replaced": r["id"], "reason": why, "by": rep["id"]})
        rep = dict(rep, replaces=r["id"], id=r["id"], reserve_id=rep["id"])
        new_primary.append(rep)
    d.update(primary=new_primary, reserve=reserve, swaps=swaps)
    (OUT / "faults_table.json").write_text(json.dumps(d, indent=1))
    print(f"validated {len(new_primary)} primaries; swaps={swaps}")
    shutil.rmtree(sf.SF, ignore_errors=True)


def tests_sha():
    files = subprocess.run(["git", "ls-files", "tests"], cwd=REAL, capture_output=True, text=True).stdout.split()
    lines = subprocess.run(["sha256sum", *files], cwd=REAL, capture_output=True, text=True).stdout
    return hashlib.sha256(lines.encode()).hexdigest()


def table_sha():
    return hashlib.sha256((OUT / "faults_table.json").read_bytes()).hexdigest()


def freeze():
    sf = _sf()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REAL, capture_output=True, text=True).stdout.strip()
    stage7 = [s for s in ("score_listener_study", "score_repair_audit", "score_oracle_indep")
              if "--selfcheck" in (REAL / "src" / f"{s}.py").read_text() or "--self-check" in (REAL / "src" / f"{s}.py").read_text()]
    fz = {"faults_table_sha256": table_sha(), "tests_tree_sha256": tests_sha(), "head": head,
          "columns_pooled": ["pytest_all"] + [t for t in sf.HARNESS_TESTS if t not in sf.SUPPLEMENTARY],
          "columns_supplementary": sf.SUPPLEMENTARY, "stage7_selfcheck_scorers_existing_at_freeze_not_in_headline": stage7}
    (OUT / "FREEZE.json").write_text(json.dumps(fz, indent=1))
    print(json.dumps(fz, indent=1))


def run():
    fz = json.loads((OUT / "FREEZE.json").read_text())
    if tests_sha() != fz["tests_tree_sha256"] or table_sha() != fz["faults_table_sha256"]:
        print("REFUSING: tests/ or table hash differs from FREEZE.json")
        sys.exit(3)
    sf = _sf()
    d = load_table()
    sf.MUTATIONS = as_mutations(d["primary"])
    sf.SF.mkdir(parents=True, exist_ok=True)
    # pytest deps: reuse existing target if present
    old = REAL / "tmp" / "sf" / "_deps"
    if not sf.DEPS.exists():
        if old.exists():
            import shutil
            shutil.copytree(old, sf.DEPS)
        else:
            subprocess.run([sf.PY, "-m", "pip", "install", "-q", "--target", str(sf.DEPS), "pytest"], check=True)
    argv = ["seeded_faults.py", "run"] + sys.argv[2:]
    sys.argv = argv
    sf.main()


if __name__ == "__main__":
    {"enumerate": enumerate_sites, "pick": pick, "validate": validate, "freeze": freeze, "run": run}[sys.argv[1]]()
