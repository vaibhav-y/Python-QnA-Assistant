// Build the project slide deck. Run: NODE_PATH=$(npm root -g) node slides/build_deck.js
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" x 5.625"
pres.author = "Vaibhav Yadav";
pres.title = "Python Q&A Assistant";

// ---- palette ----
const DARK = "0E2A38", DARK2 = "13384A";
const TEAL = "0D9488", TEAL_LT = "5EEAD4";
const AMBER = "F59E0B";
const INK = "1E293B", MUTE = "64748B";
const LITE = "F1F5F9", TINT = "F0FDFA", LINE = "E2E8F0";
const WHITE = "FFFFFF", ICE = "CADCFC";
const HF = "Georgia", BF = "Calibri";

const shadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.12 });

function kicker(s, text, color) {
  s.addText(text.toUpperCase(), { x: 0.6, y: 0.36, w: 9, h: 0.3, fontFace: BF, fontSize: 12, bold: true, color: color || TEAL, charSpacing: 2, margin: 0 });
}
function title(s, text, color) {
  s.addText(text, { x: 0.6, y: 0.66, w: 8.8, h: 0.72, fontFace: HF, fontSize: 30, bold: true, color: color || INK, margin: 0 });
}
function card(s, x, y, w, h, fill, border) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill || LITE }, line: { color: border || LINE, width: 1 }, shadow: shadow() });
}
function marker(s, x, y, color) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.12, h: 0.12, fill: { color: color || TEAL } });
}
function bullets(s, items, opt) {
  const rt = items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: true, color: opt.color || INK, fontSize: opt.fontSize || 12.5, paraSpaceAfter: opt.gap != null ? opt.gap : 6 } }));
  s.addText(rt, { x: opt.x, y: opt.y, w: opt.w, h: opt.h, fontFace: BF, valign: "top", margin: 0 });
}

// ============ Slide 1 — Title ============
let s = pres.addSlide();
s.background = { color: DARK };
s.addShape(pres.shapes.OVAL, { x: 7.4, y: -1.7, w: 5.2, h: 5.2, fill: { color: TEAL, transparency: 82 }, line: { type: "none" } });
s.addShape(pres.shapes.OVAL, { x: 8.9, y: 3.4, w: 3.2, h: 3.2, fill: { color: TEAL_LT, transparency: 88 }, line: { type: "none" } });
s.addText("RAG  ·  STACK OVERFLOW  ·  GROUNDED ANSWERS", { x: 0.7, y: 1.25, w: 8.6, h: 0.3, fontFace: BF, fontSize: 13, bold: true, color: TEAL_LT, charSpacing: 2, margin: 0 });
s.addText("Python Programming\nQ&A Assistant", { x: 0.66, y: 1.7, w: 8.6, h: 1.7, fontFace: HF, fontSize: 46, bold: true, color: WHITE, lineSpacingMultiple: 0.98, margin: 0 });
s.addText("Retrieval-augmented answers over Stack Overflow Python Q&A — with citations.", { x: 0.7, y: 3.55, w: 8.2, h: 0.5, fontFace: BF, fontSize: 17, color: ICE, margin: 0 });
s.addText([{ text: "Built by  ", options: { color: "94A3B8" } }, { text: "Vaibhav Yadav", options: { color: WHITE, bold: true } }], { x: 0.7, y: 4.35, w: 8, h: 0.35, fontFace: BF, fontSize: 15, margin: 0 });
s.addText("FastAPI  ·  FAISS  ·  bge-small  ·  Groq Llama 3.3 70B", { x: 0.7, y: 5.0, w: 8.6, h: 0.35, fontFace: BF, fontSize: 13, color: "94A3B8", margin: 0 });

// ============ Slide 2 — What I built ============
s = pres.addSlide();
s.background = { color: WHITE };
kicker(s, "Overview"); title(s, "What I built");
s.addText("A RAG assistant that answers Python questions grounded in real Stack Overflow Q&A — and returns the source links, so answers are verifiable rather than hallucinated.", { x: 0.6, y: 1.55, w: 4.7, h: 1.2, fontFace: BF, fontSize: 14.5, color: INK, margin: 0, valign: "top" });
bullets(s, [
  "Retrieves the closest Q&A pairs from a 20k-vector FAISS index",
  "Groq Llama 3.3 70B composes a grounded, cited answer",
  "Declines when the context doesn't fit — no hallucination",
  "Two entry points to one pipeline: FastAPI API + Streamlit UI",
], { x: 0.62, y: 2.85, w: 4.7, h: 2.3, fontSize: 13.5 });

// deliverables card
card(s, 5.6, 1.55, 3.8, 3.55, TINT, TEAL_LT);
marker(s, 5.85, 1.82);
s.addText("Deliverables", { x: 6.05, y: 1.72, w: 3.2, h: 0.35, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0 });
const delivs = ["RAG pipeline (retrieve → prompt → generate)", "FastAPI: /ask, /health, /reindex", "Streamlit chat UI", "8 automated API tests (pytest)", "Evaluation: 10 queries + observations", "Dockerfile + README + .env.example"];
s.addText(delivs.map((t) => ({ text: "✓  " + t, options: { breakLine: true, color: INK, fontSize: 12, paraSpaceAfter: 9, bullet: false } })), { x: 6.0, y: 2.25, w: 3.25, h: 2.7, fontFace: BF, valign: "top", margin: 0 });

// ============ Slide 3 — Architecture ============
s = pres.addSlide();
s.background = { color: WHITE };
kicker(s, "Architecture"); title(s, "How it fits together");

function flowBox(x, y, w, h, label, fill, txt, border) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: fill }, line: { color: border || TEAL_LT, width: 1 }, shadow: shadow() });
  s.addText(label, { x: x + 0.04, y, w: w - 0.08, h, align: "center", valign: "middle", fontFace: BF, fontSize: 11, bold: true, color: txt || INK, margin: 1 });
}
function arrow(x, y, w) {
  s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: TEAL, width: 1.75, endArrowType: "triangle" } });
}

// OFFLINE band
s.addText("OFFLINE  —  build the index once", { x: 0.7, y: 1.5, w: 8, h: 0.28, fontFace: BF, fontSize: 12, bold: true, color: TEAL, charSpacing: 1, margin: 0 });
const oy = 1.85, oh = 0.82, ow = 1.85, og = 0.27;
let ox = 0.7;
const off = [["Stack Overflow\nCSVs", TINT], ["Clean + filter\n(Score ≥ 5)", TINT], ["Embed\n(bge-small)", TINT], ["FAISS index\n(20k vectors)", "CCFBF1"]];
off.forEach((b, i) => { flowBox(ox, oy, ow, oh, b[0], b[1], INK); if (i < off.length - 1) arrow(ox + ow + 0.02, oy + oh / 2, og - 0.04); ox += ow + og; });

// link caption
s.addText("The prebuilt index is loaded once at startup and reused for every query.", { x: 0.7, y: 2.92, w: 8.6, h: 0.3, fontFace: BF, fontSize: 11.5, italic: true, color: MUTE, margin: 0 });

// ONLINE band
s.addText("ONLINE  —  serve  (FastAPI /ask  ·  Streamlit UI)", { x: 0.7, y: 3.32, w: 8.6, h: 0.28, fontFace: BF, fontSize: 12, bold: true, color: TEAL, charSpacing: 1, margin: 0 });
const ny = 3.67, nh = 0.82, nw = 1.55, ng = 0.2;
let nx = 0.7;
const on = [["User\nquery", LITE, INK, LINE], ["Embed\nquery", LITE, INK, LINE], ["FAISS\ntop-k", "CCFBF1", INK, TEAL_LT], ["Groq\nLlama 3.3 70B", TEAL, WHITE, TEAL], ["Answer +\ncitations", LITE, INK, LINE]];
on.forEach((b, i) => { flowBox(nx, ny, nw, nh, b[0], b[1], b[2], b[3]); if (i < on.length - 1) arrow(nx + nw + 0.01, ny + nh / 2, ng - 0.02); nx += nw + ng; });

// ============ Slide 4 — Key design decisions ============
s = pres.addSlide();
s.background = { color: WHITE };
kicker(s, "Decisions"); title(s, "Key design decisions");
const decs = [
  ["One vector per URL", "Embed each Q&A pair whole — no chunking. Pairs are coherent units; chunking fragments them."],
  ["Build-time filtering", "Index only Score ≥ 5 questions that have a positively-scored answer."],
  ["Grounded, or it declines", "The prompt forbids guessing when the retrieved context is weak."],
  ["Local embeddings + FAISS", "Free, fast, and ships as a portable file artifact — no vector-DB service."],
  ["Groq free-tier LLM", "Llama 3.3 70B — strong generation at zero cost on the free tier."],
  ["One shared indexer", "CLI, API, and UI all reuse a single build path (app/indexer.py)."],
];
const cw = 2.75, ch = 1.5, cgx = 0.3, cgy = 0.32;
let cx0 = 0.6, cy0 = 1.6;
decs.forEach((d, i) => {
  const col = i % 3, row = Math.floor(i / 3);
  const x = cx0 + col * (cw + cgx), y = cy0 + row * (ch + cgy);
  card(s, x, y, cw, ch, LITE, LINE);
  marker(s, x + 0.22, y + 0.24);
  s.addText(d[0], { x: x + 0.44, y: y + 0.16, w: cw - 0.6, h: 0.32, fontFace: HF, fontSize: 14, bold: true, color: TEAL, margin: 0 });
  s.addText(d[1], { x: x + 0.24, y: y + 0.56, w: cw - 0.46, h: ch - 0.7, fontFace: BF, fontSize: 11.5, color: INK, margin: 0, valign: "top" });
});

// ============ Slide 5 — Testing & quality ============
s = pres.addSlide();
s.background = { color: WHITE };
kicker(s, "Validation"); title(s, "Testing & quality");
bullets(s, [
  "10 diverse queries run end-to-end; the 8 in-scope ones all accurate, with runnable code + citations",
  "Grounding holds: an out-of-scope CSS question was declined, not hallucinated",
  "Dataset-age limitation surfaced: misses Python 3.9+ dict-merge (corpus is ~2008–2016)",
  "8 automated API tests pass (RAG layer mocked)",
], { x: 0.62, y: 1.65, w: 4.6, h: 3.3, fontSize: 13 });

s.addText("Latency by query (seconds)", { x: 5.45, y: 1.55, w: 4.0, h: 0.3, fontFace: BF, fontSize: 12.5, bold: true, color: INK, margin: 0 });
s.addChart(pres.charts.BAR, [{ name: "Latency (s)", labels: ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"], values: [2.9, 1.3, 1.0, 1.4, 4.6, 8.8, 9.3, 19.7, 11.6, 19.8] }], {
  x: 5.3, y: 1.85, w: 4.25, h: 2.85, barDir: "col", chartColors: [TEAL], showLegend: false, showTitle: false,
  catAxisLabelColor: MUTE, valAxisLabelColor: MUTE, catAxisLabelFontSize: 9, valAxisLabelFontSize: 9,
  valGridLine: { color: LINE, size: 0.5 }, catGridLine: { style: "none" },
});
s.addText("Retrieval is sub-millisecond; latency tracks answer length (generation-bound).", { x: 5.3, y: 4.75, w: 4.25, h: 0.4, fontFace: BF, fontSize: 10.5, italic: true, color: MUTE, margin: 0 });

// ============ Slide 6 — Scaling 1/2 ============
s = pres.addSlide();
s.background = { color: WHITE };
kicker(s, "Scale · 100+ users  (1/2)"); title(s, "Latency & async");
function colCard(x, header, items) {
  card(s, x, 1.6, 4.25, 3.45, LITE, LINE);
  marker(s, x + 0.26, 1.86);
  s.addText(header, { x: x + 0.48, y: 1.76, w: 3.6, h: 0.35, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0 });
  bullets(s, items, { x: x + 0.3, y: 2.25, w: 3.7, h: 2.6, fontSize: 12.5, gap: 8 });
}
colCard(0.6, "Latency", [
  "Pre-load the index at startup (already done)",
  "Swap flat FAISS → ANN (HNSW / IVF)",
  "Stream tokens for fast time-to-first-byte",
  "Smaller / faster model on the hot path",
]);
colCard(5.15, "Async & concurrency", [
  "Async endpoints + async Groq client",
  "Gunicorn with multiple Uvicorn workers",
  "Stateless app behind a load balancer",
  "Autoscale on CPU / requests-per-second",
]);

// ============ Slide 7 — Scaling 2/2 ============
s = pres.addSlide();
s.background = { color: WHITE };
kicker(s, "Scale · 100+ users  (2/2)"); title(s, "Data, caching & cost");
const sc = [
  ["Vector DB", ["FAISS single-node → managed Qdrant / pgvector", "One shared store across all workers", "Rebuild offline, not in the serving process"]],
  ["Caching", ["Redis exact-match query cache", "Semantic cache: reuse if query cosine ≥ 0.95", "LLM prompt caching; cache hot embeddings"]],
  ["Cost", ["Semantic cache skips most LLM calls", "Groq paid tier or provider fallback", "Per-user rate limits + token/$ dashboards"]],
];
const tw = 2.95, tgx = 0.22; let tx = 0.6;
sc.forEach(([h, items]) => {
  card(s, tx, 1.6, tw, 3.45, LITE, LINE);
  marker(s, tx + 0.24, 1.86);
  s.addText(h, { x: tx + 0.45, y: 1.76, w: tw - 0.6, h: 0.35, fontFace: HF, fontSize: 15, bold: true, color: TEAL, margin: 0 });
  bullets(s, items, { x: tx + 0.27, y: 2.25, w: tw - 0.45, h: 2.6, fontSize: 11.5, gap: 9 });
  tx += tw + tgx;
});

// ============ Slide 8 — Limitations & roadmap ============
s = pres.addSlide();
s.background = { color: DARK };
kicker(s, "Wrap-up", TEAL_LT); title(s, "Limitations & what's next", WHITE);
function darkCol(x, header, items) {
  card(s, x, 1.6, 4.25, 2.95, DARK2, "1F4A5E");
  marker(s, x + 0.26, 1.86, TEAL_LT);
  s.addText(header, { x: x + 0.48, y: 1.76, w: 3.6, h: 0.35, fontFace: HF, fontSize: 16, bold: true, color: WHITE, margin: 0 });
  bullets(s, items, { x: x + 0.3, y: 2.25, w: 3.7, h: 2.1, color: ICE, fontSize: 12.5, gap: 8 });
}
darkCol(0.6, "Known limits", [
  "Dataset ~2008–2016 — can miss newer idioms",
  "/reindex is memory-heavy and per-worker",
  "Retrieval ranking occasionally imperfect",
]);
darkCol(5.15, "Roadmap", [
  "Recency filter / fresher corpus",
  "Cross-encoder reranker for precision",
  "Managed vector DB + semantic cache",
  "Streaming answers in the UI",
]);
s.addText("Built free end-to-end:  Groq  +  bge-small  +  FAISS.", { x: 0.6, y: 4.8, w: 8.8, h: 0.4, fontFace: BF, fontSize: 13, bold: true, color: TEAL_LT, align: "center", margin: 0 });

pres.writeFile({ fileName: "slides/Python_QnA_Assistant.pptx" }).then((f) => console.log("wrote " + f));
