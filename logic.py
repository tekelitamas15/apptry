"""
Problem generation and answer checking for the factorisation game.

Kept free of tkinter so it can be tested on its own:
    python factor_logic.py
"""

import random
from math import gcd

# sympy is optional: without it we fall back to exact token matching.
try:
    import sympy as sp
    from sympy.parsing.sympy_parser import (
        parse_expr, standard_transformations, implicit_multiplication_application)
    TRANSFORMS = standard_transformations + (implicit_multiplication_application,)
    HAVE_SYMPY = True
except ImportError:                                    # pragma: no cover
    HAVE_SYMPY = False

VARS = ["x", "y", "z", "t"]
LEVEL_NAMES = {1: "common factor", 2: "common factor with a variable",
               3: "difference of squares"}


class Problem:
    """display: what the player sees.   source: parseable form.   answer: token list."""

    def __init__(self, display, source, answer, level):
        self.display = display
        self.source = source
        self.answer = answer
        self.level = level
        self.expr = parse_expr(source, transformations=TRANSFORMS) if HAVE_SYMPY else None


def _coeff(n):
    """Tokens for a coefficient: 1 is invisible in algebra, so emit nothing."""
    return [] if n == 1 else [str(n)]


def _show(n):
    return "" if n == 1 else str(n)


# --------------------------------------------------------------- generators
def level_1():
    """k*a*u + k*b*v   ->   k(a*u + b*v)"""
    while True:
        k, a, b = random.randint(2, 6), random.randint(1, 6), random.randint(1, 6)
        if gcd(a, b) == 1:
            break
    u, v = random.sample(VARS, 2)
    s = random.choice(["+", "-"])

    display = f"{k*a}{u} {s} {k*b}{v}"
    source = f"{k*a}*{u} {s} {k*b}*{v}"
    answer = [str(k), "("] + _coeff(a) + [u, s] + _coeff(b) + [v, ")"]
    return Problem(display, source, answer, 1)


def level_2():
    """k*a*u^2 + k*b*u*v   ->   k*u(a*u + b*v)"""
    while True:
        k, a, b = random.randint(2, 5), random.randint(1, 5), random.randint(1, 5)
        if gcd(a, b) == 1:
            break
    u, v = random.sample(VARS, 2)
    s = random.choice(["+", "-"])

    display = f"{k*a}{u}\u00b2 {s} {k*b}{u}{v}"
    source = f"{k*a}*{u}**2 {s} {k*b}*{u}*{v}"
    answer = [str(k), u, "("] + _coeff(a) + [u, s] + _coeff(b) + [v, ")"]
    return Problem(display, source, answer, 2)


def level_3():
    """(a*u)^2 - (b*v)^2   ->   (a*u - b*v)(a*u + b*v)

    Half the time the second square is a plain number, which keeps it short.
    """
    while True:                       # coprime, or the result factors further
        a, b = random.randint(1, 3), random.randint(2, 6)
        if gcd(a, b) == 1:
            break
    u = random.choice(VARS)

    if random.random() < 0.5:                       # u^2 - b^2
        display = f"{_show(a*a)}{u}\u00b2 - {b*b}"
        source = f"{a*a}*{u}**2 - {b*b}"
        left, right = _coeff(a) + [u], [str(b)]
    else:                                           # (a u)^2 - (b v)^2
        v = random.choice([w for w in VARS if w != u])
        display = f"{_show(a*a)}{u}\u00b2 - {_show(b*b)}{v}\u00b2"
        source = f"{a*a}*{u}**2 - {b*b}*{v}**2"
        left, right = _coeff(a) + [u], _coeff(b) + [v]

    answer = ["("] + left + ["-"] + right + [")", "("] + left + ["+"] + right + [")"]
    return Problem(display, source, answer, 3)


GENERATORS = {1: level_1, 2: level_2, 3: level_3}


def make_problem(level=1):
    """level may be 1, 2, 3, or 0 for a mixed bag."""
    if level == 0:
        level = random.choice([1, 2, 3])
    return GENERATORS[level]()


# -------------------------------------------------------------- distractors
def distractors(problem, count):
    """Plausible-looking tiles that do not belong in the answer."""
    used = set(problem.answer)
    pool = [str(d) for d in range(2, 10)] + VARS + ["+", "-", "(", ")"]
    tempting = [t for t in pool if t not in used]
    random.shuffle(tempting)
    # a duplicate of a sign or bracket is nastier than a stray letter
    extra = [t for t in ["+", "-", "(", ")"] if t in used]
    random.shuffle(extra)
    return (extra + tempting)[:count]


# ------------------------------------------------------------------ judging
def top_level_factors(s):
    """'3x(2x-3y)' -> ['3x', '(2x-3y)'].  None if the brackets are unbalanced.

    We split the *text* the player wrote rather than the parsed expression,
    because sympy silently rewrites products: 5*(4z-t) becomes 20z-5t on the
    spot, so the parsed tree no longer records how the answer was written.
    """
    pieces, current, depth = [], "", 0
    for ch in s:
        if ch == "(":
            if depth == 0 and current:
                pieces.append(current)
                current = ""
            depth += 1
        current += ch
        if ch == ")":
            depth -= 1
            if depth < 0:
                return None
            if depth == 0:
                pieces.append(current)
                current = ""
    if depth != 0:
        return None
    if current:
        pieces.append(current)
    return pieces


def judge(problem, tokens):
    """Return (correct?, message). Accepts any equivalent factorisation."""
    built = "".join(tokens)

    if not HAVE_SYMPY:
        if tokens == problem.answer:
            return True, "Correct!"
        return False, f"{built} is not right \u2014 try again"

    try:
        expr = parse_expr(built, transformations=TRANSFORMS)
    except Exception:
        return False, f"{built} is not a valid expression"

    if sp.simplify(expr - problem.expr) != 0:
        return False, f"{built} is not equal to the original"

    pieces = top_level_factors(built)
    if pieces is None:
        return False, f"{built} has mismatched brackets"
    if len(pieces) < 2 or not any(p.startswith("(") for p in pieces):
        return False, f"{built} is equal, but not written as a product"

    for piece in pieces:
        if not piece.startswith("("):
            continue
        try:
            group = parse_expr(piece, transformations=TRANSFORMS)
        except Exception:
            return False, f"{piece} is not a valid factor"
        content, irreducibles = sp.factor_list(group)
        if abs(content) != 1 or sum(m for _, m in irreducibles) != 1:
            return False, f"{built} is equal, but {piece} factors further"

    if tokens == problem.answer:
        return True, "Correct!"
    return True, f"Correct \u2014 {built} works too!"


# ---------------------------------------------------------------- self-test
if __name__ == "__main__":
    random.seed(0)
    print(f"sympy available: {HAVE_SYMPY}\n")
    for level in (1, 2, 3):
        print(f"--- level {level}: {LEVEL_NAMES[level]}")
        for _ in range(4):
            p = make_problem(level)
            ok, msg = judge(p, p.answer)
            print(f"  {p.display:16} -> {''.join(p.answer):18} {ok}  "
                  f"distractors={distractors(p, 2)}")
        print()