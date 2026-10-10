const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/Users/claire/.claude/skills/synced/b1e11d23-111c-4f42-b6a6-499bf920f8d3_8d8a66aa-efb5-42cb-b929-2ff7ad2dca7f/pptx/scripts/apply_theme.js");

const THEME = {
  name: "Currency Markets",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B1F3A",
    lt1: "FFFFFF",
    dk2: "163152",
    lt2: "EEF3F8",
    accent1: "C4A35A",
    accent2: "1D6A6A",
    accent3: "B23A48",
    accent4: "3D5A80",
    accent5: "5C6B7A",
    accent6: "8B6914",
    hlink: "1D6A6A",
    folHlink: "0B1F3A",
  },
};

const GOLD = "C4A35A";
const TEAL = "1D6A6A";
const NAVY = "0B1F3A";
const RISK = "B23A48";
const ICE = "EEF3F8";
const MUTED = "5C6B7A";

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "Designing and Testing Global Trading Strategies";
  pres.author = "MFE 230GB";
  pres.subject = "MFE 230GB Final Project, October 8, 2026";
  const C = pres.SchemeColor;

  function addHBarChart(slide, items, box) {
    const labelW = box.labelW;
    const n = items.length;
    const titleH = box.title ? 0.38 : 0;
    if (box.title) {
      slide.addText(box.title, {
        x: box.x, y: box.y, w: box.w, h: 0.34, fontSize: 12, color: NAVY,
        margin: 0, isTextBox: true, objectName: box.name + "-title",
      });
    }
    const plotY = box.y + titleH;
    const rowH = (box.h - titleH) / n;
    const barW = box.w - labelW - 0.72;
    const span = box.max - box.min;
    const originX = box.x + labelW + ((0 - box.min) / span) * barW;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: originX, y: plotY + 0.04, w: 0.012, h: n * rowH - 0.12,
      fill: { color: "C5CDD6" }, objectName: box.name + "-zero",
    });
    items.forEach((it, i) => {
      const y = plotY + i * rowH;
      slide.addText(it.label, {
        x: box.x, y, w: labelW - 0.1, h: rowH * 0.85,
        fontSize: 12, color: NAVY, align: "right", valign: "middle",
        margin: 0, isTextBox: true, objectName: box.name + "-lab-" + i,
      });
      const mag = Math.abs(it.value) / span * barW;
      const fill = it.value >= 0 ? box.pos : box.neg;
      const bx = it.value >= 0 ? originX : originX - mag;
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: bx, y: y + rowH * 0.22, w: Math.max(mag, 0.05), h: rowH * 0.38,
        rectRadius: 0.04, fill: { color: fill }, objectName: box.name + "-bar-" + i,
      });
      const valStr = it.fmt || it.value.toFixed(2);
      slide.addText(valStr, {
        x: originX + (it.value >= 0 ? mag : 0) + 0.06, y, w: 0.72, h: rowH * 0.85,
        fontSize: 12, color: NAVY, valign: "middle", align: "left",
        margin: 0, isTextBox: true, objectName: box.name + "-val-" + i,
      });
    });
  }

  pres.defineSlideMaster({
    title: "TITLE",
    background: { color: NAVY },
    objects: [
      {
        placeholder: {
          options: {
            name: "title",
            type: "title",
            x: 0.7,
            y: 2.15,
            w: 11.9,
            h: 1.7,
            fontSize: 40,
            bold: true,
            color: C.background1,
            margin: 0,
            align: "left",
            valign: "top",
          },
          text: "Title",
        },
      },
    ],
  });

  pres.defineSlideMaster({
    title: "SECTION",
    background: { color: NAVY },
    objects: [
      {
        placeholder: {
          options: {
            name: "kicker",
            type: "body",
            x: 0.7,
            y: 2.55,
            w: 11.9,
            h: 0.4,
            fontSize: 14,
            bold: true,
            color: C.accent1,
            margin: 0,
          },
          text: "Section",
        },
      },
      {
        placeholder: {
          options: {
            name: "title",
            type: "body",
            x: 0.7,
            y: 3.0,
            w: 11.9,
            h: 1.4,
            fontSize: 40,
            bold: true,
            color: C.background1,
            margin: 0,
            align: "left",
          },
          text: "Section title",
        },
      },
    ],
  });

  pres.defineSlideMaster({
    title: "LIGHT",
    background: { color: "FFFFFF" },
    objects: [
      {
        placeholder: {
          options: {
            name: "title",
            type: "title",
            x: 0.5,
            y: 0.28,
            w: 12.3,
            h: 0.62,
            fontSize: 26,
            bold: true,
            color: C.text1,
            margin: 0,
            align: "center",
          },
          text: "Title",
        },
      },
      {
        text: {
          text: "MFE 230GB  ·  Currency Markets  ·  Final Project",
          options: {
            x: 0.5,
            y: 7.18,
            w: 10.2,
            h: 0.2,
            fontSize: 11,
            color: MUTED,
            margin: 0,
            isTextBox: true,
          },
        },
      },
    ],
    slideNumber: { x: 12.15, y: 7.16, fontSize: 11, color: MUTED },
  });

  pres.defineSlideMaster({
    title: "CLOSE",
    background: { color: NAVY },
    objects: [
      {
        placeholder: {
          options: {
            name: "title",
            type: "title",
            x: 0.7,
            y: 2.6,
            w: 11.9,
            h: 1.2,
            fontSize: 36,
            bold: true,
            color: C.background1,
            margin: 0,
          },
          text: "Close",
        },
      },
    ],
  });

  // ------------------------------------------------------------------
  // 1. Title
  // ------------------------------------------------------------------
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Opening" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.7, y: 1.45, w: 2.85, h: 0.38, rectRadius: 0.06,
    fill: { color: GOLD }, objectName: "kicker-pill",
  });
  s.addText("MFE 230GB  ·  OCTOBER 8, 2026", {
    x: 0.7, y: 1.45, w: 2.85, h: 0.38, fontSize: 10, bold: true, color: NAVY,
    align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "kicker-text",
  });
  s.addText("Designing and Testing\nGlobal Trading Strategies", { placeholder: "title" });
  s.addText("Two economically identified strategies — one in G10 rates and FX, one in emerging-market terms of trade — both using prediction markets as the alternative data the course asked for.", {
    x: 0.7, y: 4.05, w: 10.5, h: 0.95, fontSize: 16, color: "D5DEE8", margin: 0, isTextBox: true,
    objectName: "subtitle",
  });
  s.addText("Short class presentation  ·  Fall 2026  ·  Haas School of Business", {
    x: 0.7, y: 6.85, w: 10, h: 0.28, fontSize: 13, color: GOLD, margin: 0, isTextBox: true,
    objectName: "footer-line",
  });
  s.addNotes("Open with the assignment, not the Sharpe. The project grades economic mechanism first. State that we built two distinct strategies that share a theme — prices move when information and demand move, not when the announcement prints — then name them: Policy Path in OECD markets, Terms of Trade in EM.");

  // ------------------------------------------------------------------
  // 2. The answer
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Opening" });
  s.addText("One theme, two distinct books", { placeholder: "title" });
  s.addText("Prices at horizons under a year are mostly demand and information flow, not scheduled macro. We trade that idea in two universes that cannot be copies of each other.", {
    x: 0.5, y: 0.95, w: 12.3, h: 0.5, fontSize: 14, color: MUTED, margin: 0, isTextBox: true, italic: true,
    objectName: "lede",
  });

  // Card 1
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.55, w: 6.0, h: 5.35, rectRadius: 0.1,
    fill: { color: ICE }, objectName: "card-s1",
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.72, y: 1.78, w: 1.55, h: 0.32, rectRadius: 0.05,
    fill: { color: NAVY }, objectName: "pill-s1",
  });
  s.addText("STRATEGY 1  ·  OECD", {
    x: 0.72, y: 1.78, w: 1.55, h: 0.32, fontSize: 10, bold: true, color: "FFFFFF",
    align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "pill-s1-t",
  });
  s.addText("Policy Path", {
    x: 0.72, y: 2.22, w: 5.55, h: 0.45, fontSize: 26, bold: true, color: NAVY, margin: 0, isTextBox: true, objectName: "s1-name",
  });
  s.addText("G10 FX forwards plus G7 duration. Prediction-market changes in the Fed path, recession odds, and elections are treated as demand shifters — the Topic 4 / Topic 5 object — not as a second macro forecast.", {
    x: 0.72, y: 2.72, w: 5.55, h: 1.15, fontSize: 14, color: "1A1A1A", margin: 0, isTextBox: true, objectName: "s1-body",
  });
  s.addText([
    { text: "Universe", options: { bold: true, breakLine: false } },
    { text: "  AUD, CAD, CHF, EUR, GBP, JPY, NOK, NZD, SEK; US/DE/JP 10-year", options: { breakLine: true } },
    { text: "Horizon", options: { bold: true, breakLine: false } },
    { text: "  Weekly rebalance, 10% vol target", options: { breakLine: true } },
    { text: "Alt data", options: { bold: true, breakLine: false } },
    { text: "  Kalshi + Polymarket ΔP and cross-platform disagreement", options: { breakLine: false } },
  ], {
    x: 0.72, y: 4.0, w: 5.55, h: 1.35, fontSize: 13, color: "1A1A1A", margin: 0, isTextBox: true,
    paraSpaceAfter: 8, objectName: "s1-spec",
  });
  s.addText("Condition G10 carry on global risk. Do not run it raw — it has not paid since 2010.", {
    x: 0.72, y: 5.5, w: 5.55, h: 1.05, fontSize: 14, italic: true, color: TEAL, margin: 0, isTextBox: true, objectName: "s1-hook",
  });

  // Card 2
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.75, y: 1.55, w: 6.05, h: 5.35, rectRadius: 0.1,
    fill: { color: ICE }, objectName: "card-s2",
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.97, y: 1.78, w: 1.85, h: 0.32, rectRadius: 0.05,
    fill: { color: TEAL }, objectName: "pill-s2",
  });
  s.addText("STRATEGY 2  ·  EM / NDF", {
    x: 6.97, y: 1.78, w: 1.85, h: 0.32, fontSize: 10, bold: true, color: "FFFFFF",
    align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "pill-s2-t",
  });
  s.addText("Terms of Trade", {
    x: 6.97, y: 2.22, w: 5.6, h: 0.45, fontSize: 26, bold: true, color: NAVY, margin: 0, isTextBox: true, objectName: "s2-name",
  });
  s.addText("Long oil-exporter EM FX versus oil-importer EM FX, but only when the terms-of-trade shock is on — Brent moves, or prediction-market odds of a supply disruption jump. Same mechanism as Topic 3; different assets, NDFs, and crash risks.", {
    x: 6.97, y: 2.72, w: 5.6, h: 1.15, fontSize: 14, color: "1A1A1A", margin: 0, isTextBox: true, objectName: "s2-body",
  });
  s.addText([
    { text: "Universe", options: { bold: true, breakLine: false } },
    { text: "  BRL, CLP, COP, ZAR vs INR, THB, CNY via NDF/spot", options: { breakLine: true } },
    { text: "Horizon", options: { bold: true, breakLine: false } },
    { text: "  Weekly, dollar-neutral, 12% vol target", options: { breakLine: true } },
    { text: "Alt data", options: { bold: true, breakLine: false } },
    { text: "  Geopolitical / OPEC contracts + Brent; not just the oil print", options: { breakLine: false } },
  ], {
    x: 6.97, y: 4.0, w: 5.6, h: 1.35, fontSize: 13, color: "1A1A1A", margin: 0, isTextBox: true,
    paraSpaceAfter: 8, objectName: "s2-spec",
  });
  s.addText("A static exporter–importer book does not pay. Timing the ToT shock does.", {
    x: 6.97, y: 5.5, w: 5.6, h: 1.05, fontSize: 14, italic: true, color: TEAL, margin: 0, isTextBox: true, objectName: "s2-hook",
  });
  s.addNotes("One minute on this slide. Emphasize they are not the same trade in two listings: OECD uses policy-path prediction markets into G10 FX and bonds; EM uses commodity ToT and geopolitical contracts into NDFs. Shared theme, different universes, different crashes.");

  // ------------------------------------------------------------------
  // 3. Course map
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Opening" });
  s.addText("What we take from each topic", { placeholder: "title" });

  const topics = [
    { n: "01", t: "Instruments", d: "Spot, forwards, NDFs, and the spread/liquidity gap between G10 and EM. Strategy 2 is an NDF book on purpose." },
    { n: "02", t: "Regimes", d: "EM is not a dirty float of G10. Reserves, the trilemma, and convertibility change both the signal and the crash." },
    { n: "03", t: "Parities", d: "CIP holds; UIP and short-run PPP do not. Carry is a downside-risk premium. Fiscal news can flip the yield–FX sign. A 10% ToT shock appreciates the real exchange rate." },
    { n: "04", t: "Order flow", d: "Macro explains ≤5% of monthly FX variance; one order-flow series explained 64% of daily DM/USD. News is priced in the trade, not the release window." },
    { n: "05", t: "Demand", d: "Latent demand accounts for 82% of exchange-rate variation. Elasticities are 1–30, not thousands. The dollar’s specialness is ~1.4% a year." },
  ];
  topics.forEach((tp, i) => {
    const y = 1.02 + i * 1.15;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y, w: 12.3, h: 1.05, rectRadius: 0.08,
      fill: { color: ICE }, objectName: `topic-row-${i}`,
    });
    s.addText(tp.n, {
      x: 0.7, y, w: 0.7, h: 1.05, fontSize: 20, bold: true, color: GOLD,
      valign: "middle", margin: 0, isTextBox: true, objectName: `topic-n-${i}`,
    });
    s.addText(tp.t, {
      x: 1.5, y: y + 0.12, w: 2.4, h: 0.8, fontSize: 16, bold: true, color: NAVY,
      valign: "middle", margin: 0, isTextBox: true, objectName: `topic-t-${i}`,
    });
    s.addText(tp.d, {
      x: 4.05, y: y + 0.14, w: 8.5, h: 0.78, fontSize: 14, color: "1A1A1A",
      valign: "middle", margin: 0, isTextBox: true, objectName: `topic-d-${i}`,
    });
  });
  s.addNotes("This slide is how we show we used the course. Do not skip it. The 5% / 64% / 82% numbers are from Topics 4 and 5 and they are the reason Strategy 1 is not another Taylor-rule regression.");

  // ------------------------------------------------------------------
  // 4. Design rules
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Opening" });
  s.addText("How we read the assignment", { placeholder: "title" });

  const rules = [
    { t: "Mechanism first", d: "A signal enters the book only if we can say who is trading and why the price must move. Backtests come after that sentence, not before." },
    { t: "Two real universes", d: "G10 can use spot, forwards, and cash bonds. EM uses NDFs and lives with convertibility and 10–20 bp costs. They are not the same strategy with a different ticker." },
    { t: "Alternative data that is a shifter", d: "Prediction-market ΔP is the demand/information shock. Disagreement across Kalshi and Polymarket is a risk-off switch, not another forecast." },
    { t: "Risk that matches the story", d: "Strategy 1 dies in a carry crash and a fiscal-dominance week. Strategy 2 dies in an oil collapse and an EM liquidity squeeze. We measure those, not just max drawdown." },
  ];
  rules.forEach((r, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 6.25;
    const y = 1.1 + row * 2.85;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 6.0, h: 2.65, rectRadius: 0.1,
      fill: { color: ICE }, objectName: `rule-${i}`,
    });
    s.addText(String(i + 1).padStart(2, "0"), {
      x: x + 0.28, y: y + 0.28, w: 0.7, h: 0.4, fontSize: 16, bold: true, color: GOLD,
      margin: 0, isTextBox: true, objectName: `rule-n-${i}`,
    });
    s.addText(r.t, {
      x: x + 1.05, y: y + 0.28, w: 4.65, h: 0.4, fontSize: 18, bold: true, color: NAVY,
      margin: 0, isTextBox: true, objectName: `rule-t-${i}`,
    });
    s.addText(r.d, {
      x: x + 0.28, y: y + 0.85, w: 5.45, h: 1.5, fontSize: 15, color: "1A1A1A",
      margin: 0, isTextBox: true, objectName: `rule-d-${i}`,
    });
  });
  s.addNotes("Kermani’s brief says complexity is not rewarded. Say that out loud. A simple, identified rule with honest crash analysis beats a black box.");

  // ------------------------------------------------------------------
  // 5. Section 1
  // ------------------------------------------------------------------
  pres.addSection({ title: "Strategy 1" });
  s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Strategy 1" });
  s.addText("STRATEGY 1  ·  DEVELOPED MARKETS", { placeholder: "kicker" });
  s.addText("Policy Path", { placeholder: "title" });
  s.addNotes("Transition: we now specify Strategy 1 at the level the brief asks — theory, signal, positions, horizon, and the risk that would falsify it.");

  // ------------------------------------------------------------------
  // 6. Hypothesis
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Strategy 1" });
  s.addText("The hypothesis is about who is trading", { placeholder: "title" });

  const stats3 = [
    { v: "≤ 5%", l: "of monthly FX variance explained by measured macro fundamentals" },
    { v: "64%", l: "of daily DM/USD changes explained by interdealer order flow in Evans–Lyons" },
    { v: "82%", l: "of exchange-rate variation attributed to latent demand in Koijen–Yogo" },
  ];
  stats3.forEach((st, i) => {
    const x = 0.5 + i * 4.2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 1.08, w: 4.0, h: 2.15, rectRadius: 0.1,
      fill: { color: ICE }, objectName: `stat-${i}`,
    });
    s.addText(st.v, {
      x, y: 1.22, w: 4.0, h: 0.85, fontSize: 36, bold: true, color: NAVY,
      align: "center", margin: 0, isTextBox: true, objectName: `stat-v-${i}`,
    });
    s.addText(st.l, {
      x: x + 0.25, y: 2.1, w: 3.5, h: 0.9, fontSize: 13, color: "1A1A1A",
      align: "center", margin: 0, isTextBox: true, objectName: `stat-l-${i}`,
    });
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 3.45, w: 12.3, h: 3.4, rectRadius: 0.1,
    fill: { color: NAVY }, objectName: "hyp-box",
  });
  s.addText("What we claim", {
    x: 0.8, y: 3.65, w: 11.7, h: 0.35, fontSize: 12, bold: true, color: GOLD, margin: 0, isTextBox: true, objectName: "hyp-k",
  });
  s.addText("A rise in prediction-market odds of a Fed cut, a recession, or a fiscal/election shock is a public but not fully priced demand shifter. It should move G10 FX and duration the way order flow does: immediately, and outside the 20-minute announcement window.", {
    x: 0.8, y: 4.1, w: 11.7, h: 1.15, fontSize: 16, color: "FFFFFF", margin: 0, isTextBox: true, objectName: "hyp-t",
  });
  s.addText("Why it is not a second Taylor rule: scheduled payrolls surprises move USD/DM ~13 bp against a 66 bp daily sigma (Topic 4). The information that matters arrives through trading. Prediction markets aggregate that information before the FOMC statement, and inelastic dollar demand (Topic 5) maps the flow into a persistent price.", {
    x: 0.8, y: 5.35, w: 11.7, h: 1.2, fontSize: 14, color: "D5DEE8", margin: 0, isTextBox: true, objectName: "hyp-why",
  });
  s.addNotes("Cite Evans-Lyons 2002, Evans-Rime, and Koijen-Yogo JPE 2026. If asked why prediction markets rather than fed-funds futures: futures are the price; prediction markets give event probabilities and cross-platform disagreement, which the brief explicitly encourages.");

  // ------------------------------------------------------------------
  // 7. Carry trap
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Strategy 1" });
  s.addText("Unconditional G10 carry is the wrong trade", { placeholder: "title" });

  addHBarChart(s, [
    { label: "Full sample", value: 0.24 },
    { label: "Since 2010", value: 0.02 },
    { label: "Low VIX", value: 0.54 },
    { label: "High VIX", value: -0.03 },
    { label: "Skip top VIX 20%", value: 0.45 },
  ], {
    x: 0.45, y: 1.15, w: 7.05, h: 5.5, labelW: 1.95,
    min: -0.15, max: 0.70, pos: GOLD, neg: RISK, name: "carry",
    title: "Developed HML carry  ·  net of bid-ask  ·  Sharpe",
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 7.7, y: 1.15, w: 5.1, h: 5.5, rectRadius: 0.1,
    fill: { color: ICE }, objectName: "carry-notes",
  });
  s.addText("Lustig–Roussanov–Verdelhan HML, developed, net of spreads. Same series as Problem Set 1.", {
    x: 7.95, y: 1.4, w: 4.65, h: 0.85, fontSize: 13, italic: true, color: MUTED, margin: 0, isTextBox: true, objectName: "carry-src",
  });
  s.addText([
    { text: "Full sample Sharpe 0.24, max drawdown −39%.", options: { breakLine: true } },
    { text: "Since 2010 the mean is ~0. The risk premium did not vanish — the crashes and the post-GFC compression ate it.", options: { breakLine: true } },
    { text: "Low-VIX months: Sharpe 0.54. High-VIX months: −0.03. Oct 2008: −13.8% in one month.", options: { breakLine: true } },
    { text: "This is Topic 3’s downside-risk CAPM, not a reason to abandon carry. It is a reason to turn it off when global risk and policy-path odds say a crash is being priced.", options: { breakLine: false } },
  ], {
    x: 7.95, y: 2.4, w: 4.65, h: 3.9, fontSize: 14, color: "1A1A1A", margin: 0, isTextBox: true,
    paraSpaceAfter: 12, objectName: "carry-bullets",
  });
  s.addNotes("This is the pset1 result put to work. Since-2010 failure is a feature of the mechanism: carry is compensation for crash risk. Strategy 1 harvests carry only when prediction-market recession odds are not rising and VIX is not in the top quintile.");

  // ------------------------------------------------------------------
  // 8. Signals
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Strategy 1" });
  s.addText("Three signals, one book", { placeholder: "title" });

  const sigs = [
    { k: "A", t: "Carry-to-vol", d: "3-month rate gap over 3-month realized FX vol, G10 vs USD. Ranked cross-section, long top three, short bottom three. Topic 3 carry-to-vol, not raw carry." },
    { k: "B", t: "Policy-path ΔP", d: "Five-day change in Polymarket and Kalshi probabilities of a next-meeting cut, a 12-month recession, and the relevant election/fiscal contract. Trade the change, never the level." },
    { k: "C", t: "Disagreement", d: "|P_Kalshi − P_Polymarket| and the contract’s implied vol. When disagreement is in the top quartile, cut gross exposure by half. This is the brief’s ‘disagreement across platforms’ clause." },
  ];
  sigs.forEach((sg, i) => {
    const x = 0.5 + i * 4.2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 1.1, w: 4.0, h: 3.2, rectRadius: 0.1,
      fill: { color: ICE }, objectName: `sig-${i}`,
    });
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.28, y: 1.35, w: 0.48, h: 0.48,
      fill: { color: GOLD }, objectName: `sig-ov-${i}`,
    });
    s.addText(sg.k, {
      x: x + 0.28, y: 1.35, w: 0.48, h: 0.48, fontSize: 16, bold: true, color: NAVY,
      align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `sig-k-${i}`,
    });
    s.addText(sg.t, {
      x: x + 0.9, y: 1.38, w: 2.85, h: 0.45, fontSize: 18, bold: true, color: NAVY,
      valign: "middle", margin: 0, isTextBox: true, objectName: `sig-t-${i}`,
    });
    s.addText(sg.d, {
      x: x + 0.28, y: 2.02, w: 3.45, h: 2.05, fontSize: 15, color: "1A1A1A",
      margin: 0, valign: "top", isTextBox: true, objectName: `sig-d-${i}`,
    });
  });
  s.addNotes("Be explicit: we never fit a kitchen-sink regression of next-week FX on twenty contracts. Three objects only. A is the cross-section, B is the overlay, C is the risk switch.");

  // ------------------------------------------------------------------
  // 9. Playbook
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Strategy 1" });
  s.addText("From signal to position, every Friday", { placeholder: "title" });

  const steps = [
    { n: "1", t: "Rank G10", d: "Sort by carry-to-vol. Long 3 / short 3, inverse-vol weights, dollar-neutral on the six legs." },
    { n: "2", t: "Read ΔP", d: "If 5-day ΔP(cut) > +5 pp: add long US duration and short USD vs EUR and JPY. Opposite if ΔP(hike) > +5 pp." },
    { n: "3", t: "Safe-haven overlay", d: "If ΔP(recession) > +5 pp: flatten carry, long JPY and CHF, short AUD and NZD. This is the Topic 3 crash-hedge." },
    { n: "4", t: "Fiscal sign check", d: "If local 10y yield and the currency move in opposite directions that week, treat it as fiscal dominance (Truss / Japan 2026). Short the currency and the long bond together." },
    { n: "5", t: "Scale", d: "Gross FX 2×, duration 1×, then vol-target the book to 10% annualized. Zero out if VIX is above its 80th percentile or disagreement is elevated." },
  ];
  steps.forEach((st, i) => {
    const y = 1.05 + i * 1.12;
    s.addShape(pres.shapes.OVAL, {
      x: 0.55, y: y + 0.22, w: 0.52, h: 0.52,
      fill: { color: NAVY }, objectName: `step-ov-${i}`,
    });
    s.addText(st.n, {
      x: 0.55, y: y + 0.22, w: 0.52, h: 0.52, fontSize: 16, bold: true, color: GOLD,
      align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `step-n-${i}`,
    });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 1.25, y, w: 11.55, h: 1.02, rectRadius: 0.08,
      fill: { color: ICE }, objectName: `step-row-${i}`,
    });
    s.addText(st.t, {
      x: 1.5, y: y + 0.1, w: 11.1, h: 0.32, fontSize: 16, bold: true, color: NAVY, margin: 0, isTextBox: true, objectName: `step-t-${i}`,
    });
    s.addText(st.d, {
      x: 1.5, y: y + 0.44, w: 11.1, h: 0.48, fontSize: 14, color: "1A1A1A", margin: 0, isTextBox: true, objectName: `step-d-${i}`,
    });
  });
  s.addNotes("Holding period is one week; no intraweek unless a contract moves more than 10 pp in a day (event rule). Leverage is explicit. Transaction costs: 2 bp round-trip G10 spot/forward, 1 bp on futures, 4 bp on cash bonds. Report net.");

  // ------------------------------------------------------------------
  // 10. Mechanism evidence
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Strategy 1" });
  s.addText("Mechanism test, not the final backtest", { placeholder: "title" });

  const mech = [
    { v: "0.45", l: "Sharpe of developed HML if we simply skip the top VIX quintile, versus 0.21 unfiltered (1990–2021, net)" },
    { v: "−13.8%", l: "Worst month: October 2008. The other crash cluster is 1998 / 2007–09 — carry’s priced risk, not noise" },
    { v: "1.4%", l: "Dollar specialness in Koijen–Yogo: foreign latent demand for US assets is worth ~1.4% a year. A policy-path shock hits an inelastic dollar book" },
  ];
  mech.forEach((m, i) => {
    const y = 1.1 + i * 1.85;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y, w: 12.3, h: 1.7, rectRadius: 0.1,
      fill: { color: ICE }, objectName: `mech-${i}`,
    });
    s.addText(m.v, {
      x: 0.75, y, w: 2.6, h: 1.7, fontSize: 28, bold: true, color: NAVY,
      valign: "middle", margin: 0, isTextBox: true, objectName: `mech-v-${i}`,
    });
    s.addText(m.l, {
      x: 3.5, y: y + 0.25, w: 9.0, h: 1.2, fontSize: 16, color: "1A1A1A",
      valign: "middle", margin: 0, isTextBox: true, objectName: `mech-l-${i}`,
    });
  });
  s.addNotes("Be honest: this is not yet the prediction-market overlay. It is the course-consistent reason the overlay should exist. Full PM history (Kalshi from 2021, Polymarket from ~2022) is the live test; fed-funds futures surprises are the long-sample proxy for robustness.");

  // ------------------------------------------------------------------
  // 11. When it loses
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Strategy 1" });
  s.addText("When Policy Path loses money", { placeholder: "title" });

  const loses = [
    { t: "Carry crash", d: "VIX spike, AUD/NZD/NOK collapse, JPY squeeze. We measure HML return on days when the global dollar factor is in its 5th percentile. The filter is supposed to cut this; if it does not, the strategy is rejected." },
    { t: "Fiscal dominance", d: "Yields up, currency down (UK 2022, Japan 2025–26). A policy-path long-duration overlay is the wrong side. The sign check in step 4 is the hedge; we still report the unhedged loss." },
    { t: "Announcement catch-up", d: "If almost all of the PM signal’s predictive power sits inside the FOMC window, we are not discovering order flow — we are trading the statement. That falsifies Topic 4 as the mechanism." },
    { t: "Crowded PM", d: "Prediction-market depth is thin versus FX. If the ΔP has already been printed in 2-year yields that morning, we are late. We require the PM move to lead, not lag, the 2s." },
  ];
  loses.forEach((ls, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 6.25;
    const y = 1.1 + row * 2.85;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 6.0, h: 2.65, rectRadius: 0.1,
      fill: { color: ICE }, objectName: `lose-${i}`,
    });
    s.addText(ls.t, {
      x: x + 0.3, y: y + 0.28, w: 5.4, h: 0.4, fontSize: 18, bold: true, color: RISK,
      margin: 0, isTextBox: true, objectName: `lose-t-${i}`,
    });
    s.addText(ls.d, {
      x: x + 0.3, y: y + 0.8, w: 5.4, h: 1.55, fontSize: 14, color: "1A1A1A",
      margin: 0, isTextBox: true, objectName: `lose-d-${i}`,
    });
  });
  s.addNotes("The brief asks for economically meaningful risk, not just max DD. Name carry crashes, fiscal episodes, and liquidity. Concentration: no single pair > 30% of gross; no single week > 25% of yearly P&L without a comment.");

  // ------------------------------------------------------------------
  // 12. Section 2
  // ------------------------------------------------------------------
  pres.addSection({ title: "Strategy 2" });
  s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Strategy 2" });
  s.addText("STRATEGY 2  ·  EMERGING MARKETS", { placeholder: "kicker" });
  s.addText("Terms of Trade", { placeholder: "title" });
  s.addNotes("Different application of the same ‘shocks that reprice demand’ idea. Here the shock is a commodity / geopolitical ToT move, not a Fed-path probability.");

  // ------------------------------------------------------------------
  // 13. Hypothesis 2
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Strategy 2" });
  s.addText("A terms-of-trade shock is a demand shock for the currency", { placeholder: "title" });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.1, w: 12.3, h: 1.55, rectRadius: 0.1,
    fill: { color: NAVY }, objectName: "tot-quote",
  });
  s.addText("Topic 3: a 10% terms-of-trade improvement appreciates the real exchange rate and raises output. Oil exporters (NOK, BRL, MXN, CAD) gain when Brent rises; importers (KRW, JPY, TWD, THB, INR, EUR) lose — after stripping out the dollar’s own swing.", {
    x: 0.8, y: 1.3, w: 11.7, h: 1.2, fontSize: 16, color: "FFFFFF", margin: 0, isTextBox: true, objectName: "tot-quote-t",
  });

  const totH = [
    { t: "Why it should predict", d: "The oil move is public. The FX move is not instantaneous because EM demand is inelastic, NDFs segment the market, and the investor base (Topic 5) adjusts with a lag. Order flow in the NDF is how the ToT news gets into the price (Topic 4)." },
    { t: "Why not always-on", d: "A static long-exporters / short-importers book is just another high-beta EM carry. In our 2010–2026 weekly sample that book’s Sharpe is ~0.04. The premium is for bearing the shock when it happens, not for sitting in BRL." },
    { t: "Role of prediction markets", d: "Brent is the realization. Polymarket/Kalshi contracts on Iran, OPEC cuts, and shipping disruption are the probability of a ToT shock before the print. ΔP should lead both oil and the exporter FX." },
  ];
  totH.forEach((h, i) => {
    const x = 0.5 + i * 4.2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y: 2.9, w: 4.0, h: 3.25, rectRadius: 0.1,
      fill: { color: ICE }, objectName: `toth-${i}`,
    });
    s.addText(h.t, {
      x: x + 0.25, y: 3.1, w: 3.5, h: 0.7, fontSize: 16, bold: true, color: NAVY, margin: 0, isTextBox: true, objectName: `toth-t-${i}`,
    });
    s.addText(h.d, {
      x: x + 0.25, y: 3.85, w: 3.5, h: 2.1, fontSize: 14, color: "1A1A1A",
      margin: 0, valign: "top", isTextBox: true, objectName: `toth-d-${i}`,
    });
  });
  s.addNotes("Connect to the 2026 lecture charts: Iran-war oil spike, rial/Treasury comovement, and Brooks on EM carry restarting after the outflow. We are not rediscovering EM carry; we are trading the ToT impulse.");

  // ------------------------------------------------------------------
  // 14. Oil betas
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Strategy 2" });
  s.addText("Dollar-controlled oil betas line up with the lecture", { placeholder: "title" });

  addHBarChart(s, [
    { label: "MXN", value: 0.029, fmt: "0.029" },
    { label: "KRW", value: 0.007, fmt: "0.007" },
    { label: "BRL", value: 0.005, fmt: "0.005" },
    { label: "THB", value: 0.002, fmt: "0.002" },
    { label: "CNY", value: -0.001, fmt: "−0.001" },
    { label: "ZAR", value: -0.002, fmt: "−0.002" },
    { label: "INR", value: -0.013, fmt: "−0.013" },
    { label: "EUR", value: -0.035, fmt: "−0.035" },
    { label: "JPY", value: -0.074, fmt: "−0.074" },
  ], {
    x: 0.4, y: 1.05, w: 7.9, h: 5.65, labelW: 0.85,
    min: -0.09, max: 0.045, pos: TEAL, neg: RISK, name: "oilb",
    title: "Weekly dFX = a + b dBrent + c dDollar   ·  2010-2019",
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 8.5, y: 1.15, w: 4.3, h: 5.5, rectRadius: 0.1,
    fill: { color: ICE }, objectName: "beta-note",
  });
  s.addText("FRED H.10 and Brent, weekly, 2010–2019. Same specification as the Topic 3 oil-shock slide: strip out the broad dollar so we are not just trading DTWEXBGS.", {
    x: 8.75, y: 1.4, w: 3.85, h: 1.5, fontSize: 13, color: "1A1A1A", margin: 0, isTextBox: true, objectName: "beta-src",
  });
  s.addText("MXN and BRL load positively. JPY, EUR, and INR load negatively. ZAR is a commodity currency that still loads on the dollar more than on oil — which is why we estimate betas rather than using a textbook exporter list.", {
    x: 8.75, y: 3.05, w: 3.85, h: 2.0, fontSize: 14, color: "1A1A1A", margin: 0, isTextBox: true, objectName: "beta-insight",
  });
  s.addText("Betas are estimated in sample and frozen for the 2020–2026 out-of-sample book.", {
    x: 8.75, y: 5.2, w: 3.85, h: 1.1, fontSize: 14, italic: true, color: TEAL, margin: 0, isTextBox: true, objectName: "beta-oos",
  });
  s.addNotes("KRW is OECD so it can appear only as a robustness pair, not in the EM book. Strategy 2 longs BRL/CLP/COP/ZAR and shorts INR/THB/CNY. MXN is the OECD commodity analogue inside Strategy 1 if we want a G10 ToT overlay — we do not mix it into Strategy 2.");

  // ------------------------------------------------------------------
  // 15. Rule + prelim
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Strategy 2" });
  s.addText("The EM book, and a first out-of-sample look", { placeholder: "title" });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.08, w: 6.1, h: 5.55, rectRadius: 0.1,
    fill: { color: ICE }, objectName: "em-rule",
  });
  s.addText("Trading rule", {
    x: 0.75, y: 1.28, w: 5.6, h: 0.35, fontSize: 16, bold: true, color: NAVY, margin: 0, isTextBox: true, objectName: "em-rule-h",
  });
  s.addText([
    { text: "Each Friday, re-estimate 3-year rolling oil betas, dollar-controlled.", options: { breakLine: true } },
    { text: "Long the two highest-beta EM names, short the two lowest, equal dollar, NDF where needed.", options: { breakLine: true } },
    { text: "Hold the LS only if last week’s Brent return is positive or 5-day ΔP(supply disruption) > +5 pp. Flip the sign if oil is down and ΔP is not rising.", options: { breakLine: true } },
    { text: "Vol-target 12%. No pair > 35% of gross. Skip a name if 1-month realized vol is above its 95th percentile (convertibility / crash filter).", options: { breakLine: false } },
  ], {
    x: 0.75, y: 1.75, w: 5.6, h: 4.55, fontSize: 15, color: "1A1A1A", margin: 0, isTextBox: true,
    paraSpaceAfter: 14, valign: "top", objectName: "em-rule-b",
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.85, y: 1.08, w: 5.95, h: 5.55, rectRadius: 0.1,
    fill: { color: NAVY }, objectName: "em-res",
  });
  s.addText("Preliminary  ·  oil-timed LS only", {
    x: 7.1, y: 1.28, w: 5.5, h: 0.3, fontSize: 12, bold: true, color: GOLD, margin: 0, isTextBox: true, objectName: "em-res-k",
  });
  s.addText("This uses Brent timing, not yet the prediction-market overlay. It is the mechanism check.", {
    x: 7.1, y: 1.62, w: 5.5, h: 0.7, fontSize: 13, color: "D5DEE8", margin: 0, isTextBox: true, objectName: "em-res-note",
  });

  const emStats = [
    { v: "0.28", l: "Sharpe, 2010–2026, oil-timed" },
    { v: "0.17", l: "Sharpe, 2020–2026 out of sample" },
    { v: "−13%", l: "Max drawdown, OOS" },
    { v: "~0.04", l: "Sharpe if we never time — rejected" },
  ];
  emStats.forEach((e, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 7.15 + col * 2.7;
    const y = 2.45 + row * 1.85;
    s.addText(e.v, {
      x, y, w: 2.5, h: 0.7, fontSize: 26, bold: true, color: "FFFFFF", margin: 0, isTextBox: true, objectName: `emv-${i}`,
    });
    s.addText(e.l, {
      x, y: y + 0.7, w: 2.5, h: 0.7, fontSize: 13, color: "D5DEE8", margin: 0, isTextBox: true, objectName: `eml-${i}`,
    });
  });
  s.addNotes("Weekly FRED sample, long BRL+THB vs short ZAR+INR based on 2010-19 betas, timed on lagged oil sign. Costs not yet deducted — EM NDF 10-20 bp will eat a lot of the 0.17. That is a feature we will show, not hide. Prediction-market overlay is the incremental test.");

  // ------------------------------------------------------------------
  // 16. When 2 loses
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Strategy 2" });
  s.addText("When Terms of Trade loses money", { placeholder: "title" });

  const lose2 = [
    { t: "Oil crash, not a ToT boom", d: "March–April 2020: Brent −35% then −23% in consecutive weeks. BRL and ZAR both sold off with global risk. A long-exporter book is a high-beta book on those weeks. Timing helps; it does not eliminate the left tail." },
    { t: "Country risk dominates oil", d: "A Brazil fiscal scare or a South Africa load-shedding / politics week can move BRL/ZAR more than Brent. We report a country-dummy regression and cap any one name at 35%." },
    { t: "NDF liquidity and convertibility", d: "INR, THB, CNY, CLP trade as NDFs (Topic 1). Spreads gap when the dollar squeezes. We haircut returns 10–20 bp round-trip and show a version that drops any pair whose 1-month vol has doubled." },
    { t: "Dollar wave", d: "If the LS is secretly a short-dollar trade, we have not isolated ToT. Every result is reported dollar-neutral and after hedging DTWEXBGS. Residual dollar beta must be near zero." },
  ];
  lose2.forEach((ls, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 6.25;
    const y = 1.1 + row * 2.85;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 6.0, h: 2.65, rectRadius: 0.1,
      fill: { color: ICE }, objectName: `l2-${i}`,
    });
    s.addText(ls.t, {
      x: x + 0.3, y: y + 0.25, w: 5.4, h: 0.5, fontSize: 16, bold: true, color: RISK, margin: 0, isTextBox: true, objectName: `l2t-${i}`,
    });
    s.addText(ls.d, {
      x: x + 0.3, y: y + 0.85, w: 5.4, h: 1.55, fontSize: 14, color: "1A1A1A", margin: 0, isTextBox: true, objectName: `l2d-${i}`,
    });
  });
  s.addNotes("March 2020 is the exhibit they will ask for. Have the week-by-week oil and BRL/ZAR numbers ready: 13 Mar oil -35%, BRL -2.6%; 20 Mar oil -23%, BRL -4.9%, ZAR -7.0%.");

  // ------------------------------------------------------------------
  // 17. Comparison
  // ------------------------------------------------------------------
  pres.addSection({ title: "Evaluation" });
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Evaluation" });
  s.addText("Same theme, different crashes", { placeholder: "title" });

  const tableRows = [
    [
      { text: "", options: { fill: { color: NAVY }, color: "FFFFFF", bold: true, align: "left" } },
      { text: "Policy Path  ·  OECD", options: { fill: { color: NAVY }, color: "FFFFFF", bold: true, align: "center" } },
      { text: "Terms of Trade  ·  EM", options: { fill: { color: NAVY }, color: "FFFFFF", bold: true, align: "center" } },
    ],
    ["Mechanism", "Inelastic dollar demand + order flow around policy-path information", "ToT shock into segmented NDF demand"],
    ["Alt data", "Kalshi / Polymarket Fed, recession, election; disagreement", "Geopolitical and OPEC contracts + Brent"],
    ["Instruments", "G10 forwards, US/DE/JP 10-year", "EM NDFs (BRL, INR, THB, CNY, CLP)"],
    ["Horizon", "Weekly, 10% vol target", "Weekly, 12% vol target"],
    ["Turns off when", "High VIX, high PM disagreement, fiscal-sign flip", "Oil crash, country-risk spike, NDF vol doubling"],
    ["Falsifier", "PM ΔP only predicts inside the FOMC window", "LS is just a dollar trade, or always-on equals timed"],
  ];

  const formatted = tableRows.map((row, ri) => {
    if (ri === 0) return row;
    return row.map((cell, ci) => ({
      text: cell,
      options: {
        fill: { color: ri % 2 === 0 ? ICE : "FFFFFF" },
        color: ci === 0 ? NAVY : "1A1A1A",
        bold: ci === 0,
        align: "left",
        valign: "middle",
      },
    }));
  });

  s.addTable(formatted, {
    x: 0.5, y: 1.1, w: 12.3, h: 5.7,
    colW: [2.1, 5.1, 5.1],
    border: [{ pt: 0 }, { pt: 0 }, { pt: 0 }, { pt: 0 }],
    fontFace: "Calibri",
    fontSize: 13,
    color: "1A1A1A",
    valign: "middle",
    align: "left",
  });
  s.addNotes("This is the ‘meaningfully different applications’ slide. If a questioner says they look similar, point at instruments, the crash that kills each, and the falsifier.");

  // ------------------------------------------------------------------
  // 18. Metrics and robustness
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Evaluation" });
  s.addText("What we will report, including the tests that can kill it", { placeholder: "title" });

  const evals = [
    { t: "Performance", d: "Cumulative excess return, mean, vol, Sharpe, max DD, turnover, hit rate — gross and after G10 2 bp / EM 15 bp round-trip." },
    { t: "Out of sample", d: "Signals and betas frozen through 2019; 2020–2026 is walk-forward. A second split: train to 2016, test 2017–19, then 2020–26." },
    { t: "Placebo", d: "Shuffle PM ΔP dates; the Sharpe must collapse. Always-on carry and always-on exporter LS are the published nulls." },
    { t: "Lead/lag", d: "PM ΔP must lead 2-year yields (S1) and Brent (S2) at least some of the time. If it only lags, we are not using alternative data." },
    { t: "Risk overlays", d: "Carry-crash dummy, oil-shock dummy, global dollar dummy, country dummies. Report beta, not a story." },
    { t: "Concentration", d: "Share of P&L from top pair, top month, and top contract. A strategy that is one week in 2026 is not a strategy." },
  ];
  evals.forEach((e, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.5 + col * 4.2;
    const y = 1.1 + row * 2.85;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 4.0, h: 2.65, rectRadius: 0.1,
      fill: { color: ICE }, objectName: `ev-${i}`,
    });
    s.addText(e.t, {
      x: x + 0.25, y: y + 0.28, w: 3.5, h: 0.45, fontSize: 16, bold: true, color: NAVY, margin: 0, isTextBox: true, objectName: `evt-${i}`,
    });
    s.addText(e.d, {
      x: x + 0.25, y: y + 0.85, w: 3.5, h: 1.5, fontSize: 14, color: "1A1A1A", margin: 0, isTextBox: true, objectName: `evd-${i}`,
    });
  });
  s.addNotes("Read the falsifiers if time is short. Faculty will care more about the placebo and the lead/lag than about a 0.1 difference in Sharpe.");

  // ------------------------------------------------------------------
  // 19. Data and replication
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Evaluation" });
  s.addText("Data, costs, and the other deliverables", { placeholder: "title" });

  const dataC = [
    { t: "Prices", d: "FRED H.10 FX, Brent, VIX, OECD 3-month and 10-year yields. Lustig currency portfolios for the G10 carry history. Bloomberg/Refinitiv NDFs for the live EM book." },
    { t: "Prediction markets", d: "Kalshi and Polymarket historical contracts: Fed decision, US recession, elections, Iran/OPEC/shipping. Store raw JSON. Document every AI prompt in the README." },
    { t: "HTML + package", d: "Self-contained page: idea, signals, equity curves, crash tables, lead/lag. Replication: data or download scripts, all notebooks, costs file, and a one-page README." },
  ];
  dataC.forEach((d, i) => {
    const y = 1.1 + i * 1.85;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y, w: 12.3, h: 1.7, rectRadius: 0.1,
      fill: { color: ICE }, objectName: `data-${i}`,
    });
    s.addText(d.t, {
      x: 0.8, y: y + 0.25, w: 2.6, h: 1.2, fontSize: 18, bold: true, color: NAVY,
      valign: "middle", margin: 0, isTextBox: true, objectName: `datat-${i}`,
    });
    s.addText(d.d, {
      x: 3.6, y: y + 0.25, w: 8.9, h: 1.2, fontSize: 15, color: "1A1A1A",
      valign: "middle", margin: 0, isTextBox: true, objectName: `datad-${i}`,
    });
  });
  s.addNotes("Use of AI is allowed but must be documented. Say we will ship prompts with the replication package. The HTML is the take-home artifact; this deck is the 10-minute argument.");

  // ------------------------------------------------------------------
  // 20. Close
  // ------------------------------------------------------------------
  s = pres.addSlide({ masterName: "CLOSE", sectionTitle: "Evaluation" });
  s.addText("What we want you to remember", { placeholder: "title" });
  s.addText("Carry and terms of trade are not dead. Unconditional versions of them are. We trade the shock that the course actually identified — a demand and information shock — with prediction markets as the alternative data, in two universes that fail in different weeks.", {
    x: 0.7, y: 3.95, w: 11.9, h: 1.4, fontSize: 18, color: "D5DEE8", margin: 0, isTextBox: true, objectName: "close-body",
  });
  s.addText("Policy Path  ·  Terms of Trade  ·  MFE 230GB", {
    x: 0.7, y: 6.7, w: 11.9, h: 0.35, fontSize: 14, color: GOLD, margin: 0, isTextBox: true, objectName: "close-kicker",
  });
  s.addNotes("Stop here. If there is time, take questions on prediction-market depth, NDF costs, and why we refused raw carry. Do not volunteer a Sharpe we have not earned on the PM overlay.");

  const out = "/Users/claire/Projects/MFE/230GB/project/MFE230GB_Final_Project_Deck.pptx";
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("Wrote", out);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
