/* Az egységkör-játék logikája - a trig_logic.py JS párja.
   Nincs függosége. A pontos értékek táblázatból jönnek, nem számformázásból. */

const NOTABLE = [0, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330];

const MINUS = "\u2212";                     // tipográfiai mínuszjel
const SQRT2 = Math.SQRT2 / 2;
const SQRT3 = Math.sqrt(3) / 2;
const EPS = 1e-9;

const MAGNITUDES = [[0, "0"], [0.5, "1/2"], [SQRT2, "\u221a2/2"],
                    [SQRT3, "\u221a3/2"], [1, "1"]];

function exact(value) {
  for (const [magnitude, text] of MAGNITUDES) {
    if (Math.abs(Math.abs(value) - magnitude) < EPS) {
      if (text === "0") return "0";
      return (value < 0 ? MINUS : "") + text;
    }
  }
  return value.toFixed(3).replace("-", MINUS);
}

function angleError(a, b) {
  const d = Math.abs(a - b) % 360;
  return Math.min(d, 360 - d);
}

function makeQuestion(arbitrary = false) {
  const degrees = arbitrary ? Math.round(Math.random() * 3600) / 10
                            : NOTABLE[Math.floor(Math.random() * NOTABLE.length)];
  const func = Math.random() < 0.5 ? "cos" : "sin";
  const rad = degrees * Math.PI / 180;

  const cos = Math.cos(rad), sin = Math.sin(rad);
  const correct = func === "cos" ? cos : sin;
  const other = func === "cos" ? sin : cos;

  const supp = (180 - degrees) * Math.PI / 180;           // pótszög: gyakori tévedés
  const suppValue = func === "cos" ? Math.cos(supp) : Math.sin(supp);

  // A hamis válaszok tipikus hibákat modelleznek, nem véletlen számok.
  const candidates = [other, -correct, -other, suppValue, -suppValue];

  const correctText = exact(correct);
  const wrong = [];
  for (const value of candidates) {
    const text = exact(value);
    if (text !== correctText && !wrong.includes(text)) wrong.push(text);
  }

  // Feltöltés, ha kevés maradt (pl. a helyes válasz 0, ilyenkor sok jelölt egybeesik).
  const pool = [];
  for (const [m] of MAGNITUDES) { pool.push(m, -m); }
  pool.sort(() => Math.random() - 0.5);
  for (const value of pool) {
    if (wrong.length >= 3) break;
    const text = exact(value);
    if (text !== correctText && !wrong.includes(text)) wrong.push(text);
  }

  const options = [...wrong.slice(0, 3), correctText].sort(() => Math.random() - 0.5);
  return {degrees, func, cos, sin, value: correct, options,
          correctIndex: options.indexOf(correctText), correctText};
}

function pointScore(errorDegrees, tolerance) {
  if (errorDegrees <= tolerance / 2) return [2, "Pontos!"];
  if (errorDegrees <= tolerance) return [1, "Elfogadva."];
  return [0, "Túl messze."];
}

if (typeof module !== "undefined") {
  module.exports = {NOTABLE, exact, angleError, makeQuestion, pointScore};
}
