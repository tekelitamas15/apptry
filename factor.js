/* Problem generation and answer checking - the JS twin of factor_logic.py.
   No dependencies. Exact integer arithmetic throughout: polynomials are stored
   as {monomial: coefficient}, where a monomial is its variables sorted and
   concatenated ("" = constant, "x" = x, "xx" = x squared, "xy" = xy).        */

const VARS = ["x", "y", "z", "t"];
const LEVEL_NAMES = {1: "common factor",
                     2: "common factor with a variable",
                     3: "difference of squares"};
const DISTRACTOR_COUNT = {1: 2, 2: 2, 3: 3};

// ------------------------------------------------------------------ helpers
const gcd = (a, b) => { a = Math.abs(a); b = Math.abs(b);
                        while (b) { [a, b] = [b, a % b]; } return a; };
const randInt = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));
const choice = arr => arr[Math.floor(Math.random() * arr.length)];
const shuffle = a => { for (let i = a.length - 1; i > 0; i--) {
                         const j = Math.floor(Math.random() * (i + 1));
                         [a[i], a[j]] = [a[j], a[i]]; } return a; };
const sample = (arr, k) => shuffle([...arr]).slice(0, k);
const mono = (...vs) => vs.sort().join("");

// -------------------------------------------------------------- polynomials
function polyAdd(a, b, sign = 1) {
  const out = {...a};
  for (const m in b) { out[m] = (out[m] || 0) + sign * b[m]; }
  return out;
}

function polyMul(a, b) {
  const out = {};
  for (const m1 in a) for (const m2 in b) {
    const m = mono(...(m1 + m2).split("").filter(Boolean));
    out[m] = (out[m] || 0) + a[m1] * b[m2];
  }
  return out;
}

function polyTrim(p) {
  const out = {};
  for (const m in p) if (p[m] !== 0) out[m] = p[m];
  return out;
}

function polyEqual(a, b) {
  a = polyTrim(a); b = polyTrim(b);
  const ka = Object.keys(a), kb = Object.keys(b);
  return ka.length === kb.length && ka.every(m => a[m] === b[m]);
}

/* Recursive descent over single characters.
   expr := ['-'] term (('+'|'-') term)*      term := factor+   (juxtaposition)
   factor := digits | variable | '(' expr ')'                                */
function parse(str) {
  let i = 0;

  function parseFactor() {
    const ch = str[i];
    if (ch === "(") {
      i++;
      const inner = parseExpr();
      if (str[i] !== ")") throw new Error("missing )");
      i++;
      return inner;
    }
    if (/[0-9]/.test(ch)) {
      let n = "";
      while (i < str.length && /[0-9]/.test(str[i])) n += str[i++];
      return {"": parseInt(n, 10)};
    }
    if (VARS.includes(ch)) { i++; return {[ch]: 1}; }
    throw new Error("unexpected " + ch);
  }

  function parseTerm() {
    let val = null;
    while (i < str.length && !"+-)".includes(str[i])) {
      const f = parseFactor();
      val = val === null ? f : polyMul(val, f);
    }
    if (val === null) throw new Error("empty term");
    return val;
  }

  function parseExpr() {
    let val = str[i] === "-" ? (i++, polyAdd({}, parseTerm(), -1)) : parseTerm();
    while (i < str.length && (str[i] === "+" || str[i] === "-")) {
      const op = str[i++];
      val = polyAdd(val, parseTerm(), op === "+" ? 1 : -1);
    }
    return val;
  }

  const result = parseExpr();
  if (i !== str.length) throw new Error("trailing input");
  return result;
}

// -------------------------------------------------------------- generators
const coeffTokens = n => (n === 1 ? [] : [String(n)]);
const show = n => (n === 1 ? "" : String(n));

function level1() {                       // k*a*u + k*b*v -> k(a*u + b*v)
  let k, a, b;
  do { k = randInt(2, 6); a = randInt(1, 6); b = randInt(1, 6); } while (gcd(a, b) !== 1);
  const [u, v] = sample(VARS, 2), s = choice(["+", "-"]), sg = s === "+" ? 1 : -1;
  return {
    level: 1,
    display: `${k * a}${u} ${s} ${k * b}${v}`,
    poly: {[u]: k * a, [v]: sg * k * b},
    answer: [String(k), "(", ...coeffTokens(a), u, s, ...coeffTokens(b), v, ")"]
  };
}

function level2() {                       // k*a*u^2 + k*b*u*v -> k*u(a*u + b*v)
  let k, a, b;
  do { k = randInt(2, 5); a = randInt(1, 5); b = randInt(1, 5); } while (gcd(a, b) !== 1);
  const [u, v] = sample(VARS, 2), s = choice(["+", "-"]), sg = s === "+" ? 1 : -1;
  return {
    level: 2,
    display: `${k * a}${u}\u00b2 ${s} ${k * b}${u}${v}`,
    poly: {[mono(u, u)]: k * a, [mono(u, v)]: sg * k * b},
    answer: [String(k), u, "(", ...coeffTokens(a), u, s, ...coeffTokens(b), v, ")"]
  };
}

function level3() {                       // (a*u)^2 - (b*v)^2 -> (au-bv)(au+bv)
  let a, b;
  do { a = randInt(1, 3); b = randInt(2, 6); } while (gcd(a, b) !== 1);
  const u = choice(VARS);
  let display, poly, left, right;

  if (Math.random() < 0.5) {                            // u^2 - b^2
    display = `${show(a * a)}${u}\u00b2 - ${b * b}`;
    poly = {[mono(u, u)]: a * a, "": -b * b};
    left = [...coeffTokens(a), u]; right = [String(b)];
  } else {                                              // (a u)^2 - (b v)^2
    const v = choice(VARS.filter(w => w !== u));
    display = `${show(a * a)}${u}\u00b2 - ${show(b * b)}${v}\u00b2`;
    poly = {[mono(u, u)]: a * a, [mono(v, v)]: -b * b};
    left = [...coeffTokens(a), u]; right = [...coeffTokens(b), v];
  }
  return {level: 3, display, poly,
          answer: ["(", ...left, "-", ...right, ")", "(", ...left, "+", ...right, ")"]};
}

const GENERATORS = {1: level1, 2: level2, 3: level3};

function makeProblem(level) {
  if (!level) level = choice([1, 2, 3]);
  return GENERATORS[level]();
}

function distractors(problem, count) {
  const used = new Set(problem.answer);
  const pool = ["2","3","4","5","6","7","8","9", ...VARS, "+", "-", "(", ")"];
  const tempting = shuffle(pool.filter(t => !used.has(t)));
  // a duplicate bracket or sign is nastier than a stray letter
  const extra = shuffle(["+", "-", "(", ")"].filter(t => used.has(t)));
  return [...extra, ...tempting].slice(0, count);
}

// ----------------------------------------------------------------- judging
/* Split what the player *wrote* into top-level factors:
   "3x(2x-3y)" -> ["3x", "(2x-3y)"].  null if the brackets do not balance.   */
function topLevelFactors(s) {
  const pieces = [];
  let current = "", depth = 0;
  for (const ch of s) {
    if (ch === "(") {
      if (depth === 0 && current) { pieces.push(current); current = ""; }
      depth++;
    }
    current += ch;
    if (ch === ")") {
      depth--;
      if (depth < 0) return null;
      if (depth === 0) { pieces.push(current); current = ""; }
    }
  }
  if (depth !== 0) return null;
  if (current) pieces.push(current);
  return pieces;
}

function judge(problem, tokens) {
  const built = tokens.join("");
  let expr;
  try { expr = parse(built); }
  catch (e) { return [false, `${built} is not a valid expression`]; }

  if (!polyEqual(expr, problem.poly))
    return [false, `${built} is not equal to the original`];

  const pieces = topLevelFactors(built);
  if (pieces === null) return [false, `${built} has mismatched brackets`];
  if (pieces.length < 2 || !pieces.some(p => p.startsWith("(")))
    return [false, `${built} is equal, but not written as a product`];

  for (const piece of pieces) {
    if (!piece.startsWith("(")) continue;
    let group;
    try { group = polyTrim(parse(piece)); }
    catch (e) { return [false, `${piece} is not a valid factor`]; }

    const content = Object.values(group).reduce((g, c) => gcd(g, c), 0);
    if (content !== 1)
      return [false, `${built} is equal, but ${piece} factors further`];

    const degree = Math.max(...Object.keys(group).map(m => m.length));
    if (degree !== 1)
      return [false, `${built} is equal, but ${piece} is not a linear factor`];
  }

  const exact = tokens.length === problem.answer.length &&
                tokens.every((t, i) => t === problem.answer[i]);
  return [true, exact ? "Correct!" : `Correct \u2014 ${built} works too!`];
}

if (typeof module !== "undefined") {          // so Node can test this file
  module.exports = {makeProblem, judge, distractors, topLevelFactors, parse,
                    polyEqual, LEVEL_NAMES, DISTRACTOR_COUNT, shuffle};
}
