// ===== ML.JS — FastAPI Integration (Port 8000) =====
const ML_BASE = "http://localhost:8001";

// ── 1. Category Predictor ─────────────────────────────────────
let mlDebounceTimer = null;
function mlPredictCategory(title) {
  clearTimeout(mlDebounceTimer);
  const chip = document.getElementById("mlCategoryChip");
  if (!chip) return;
  if (!title || title.trim().length < 3) { chip.classList.add("d-none"); return; }
  mlDebounceTimer = setTimeout(async () => {
    try {
      const res = await fetch(`${ML_BASE}/ml/predict-category`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim() })
      });
      if (!res.ok) return;
      const d = await res.json();
      chip.classList.remove("d-none");
      chip.innerHTML = `<span class="badge rounded-pill" style="background:var(--gold);color:var(--brown-dark);font-size:0.75rem;cursor:pointer"
        onclick="mlApplyCategory('${d.category}')" title="Click to apply">
        AI: ${d.category} (${d.confidence}%) — click to apply</span>`;
    } catch(e) {}
  }, 400);
}

function mlApplyCategory(cat) {
  const sel = document.getElementById("txnCategory");
  if (!sel) return;
  const known = ["Food","Clothing","Travel","Books","Entertainment","Health"];
  if (known.includes(cat)) {
    sel.value = cat;
    document.getElementById("customCatDiv")?.classList.add("d-none");
  } else {
    sel.value = "Other";
    document.getElementById("customCatDiv")?.classList.remove("d-none");
    const c = document.getElementById("customCat");
    if (c) c.value = cat;
  }
  if (typeof toggleCustom === "function") toggleCustom();
  document.getElementById("mlCategoryChip")?.classList.add("d-none");
}

// ── 2. Sentiment ──────────────────────────────────────────────
async function mlLoadSentiment(transactions, budget) {
  const el = document.getElementById("mlSentimentCard");
  if (!el) return;
  el.innerHTML = `<span class="text-muted small">Analysing spending health...</span>`;
  try {
    const res = await fetch(`${ML_BASE}/ml/sentiment`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transactions, budget })
    });
    if (!res.ok) { el.innerHTML = ""; return; }
    const d = await res.json();
    const colorMap = { success:"#1b5e20", warning:"#bf360c", danger:"#7f0000" };
    const bgMap    = { success:"#e8f5e9", warning:"#fff3e0", danger:"#ffebee" };
    el.innerHTML = `<div class="d-flex align-items-start gap-2 p-2 rounded"
      style="background:${bgMap[d.color]||"#f5f5f5"};border:1px solid ${colorMap[d.color]||"#ccc"}">
      <span style="font-size:1.6rem;line-height:1">${d.emoji}</span>
      <div>
        <div class="fw-semibold small" style="color:${colorMap[d.color]}">${d.label} — Score ${d.score}/100</div>
        <div class="small mt-1" style="color:var(--text-mid)">${d.message}</div>
      </div></div>`;
  } catch(e) {
    el.innerHTML = `<span class="text-muted small">ML server offline — run <code>python run.py</code></span>`;
  }
}

// ── 3. Auto-Summary ───────────────────────────────────────────
async function mlLoadSummary(transactions, budget) {
  const el = document.getElementById("mlSummaryText");
  if (!el) return;
  try {
    const res = await fetch(`${ML_BASE}/ml/summarize`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transactions, budget })
    });
    if (!res.ok) return;
    const d = await res.json();
    el.textContent = d.summary;
  } catch(e) {
    el.textContent = "AI summary unavailable.";
  }
}

// ── 4. Forecast ───────────────────────────────────────────────
async function mlLoadForecast(transactions) {
  const el = document.getElementById("mlForecastCard");
  if (!el) return;
  try {
    const res = await fetch(`${ML_BASE}/ml/forecast`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transactions })
    });
    if (!res.ok) return;
    const d = await res.json();
    const trendColor = d.trend === "up" ? "#bf360c" : d.trend === "down" ? "#1b5e20" : "var(--brown-main)";
    el.innerHTML = `<div class="d-flex align-items-center gap-2">
      <span style="font-size:1.5rem">${d.trend === "up" ? "📈" : d.trend === "down" ? "📉" : "📊"}</span>
      <div>
        <div class="fw-semibold small" style="color:${trendColor}">Next Month: ₹${Number(d.forecast).toLocaleString("en-IN")}</div>
        <div class="small" style="color:var(--text-muted)">${d.message}</div>
      </div></div>`;
  } catch(e) {
    el.innerHTML = `<span class="text-muted small">Forecast unavailable</span>`;
  }
}

// ── 5. Anomaly Detection ──────────────────────────────────────
async function mlLoadAnomalies(transactions) {
  if (!transactions || transactions.length < 3) return;
  try {
    const res = await fetch(`${ML_BASE}/ml/anomaly`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transactions })
    });
    if (!res.ok) return;
    const d = await res.json();
    if (!d.anomalies || d.anomalies.length === 0) return;
    const banner = document.getElementById("anomalyBanner");
    if (banner) {
      banner.classList.remove("d-none");
      banner.innerHTML = `⚠️ <strong>${d.anomalies.length} unusual expense${d.anomalies.length>1?"s":""} detected</strong> — ${d.anomalies.map(a=>`<em>${a.title}</em> (${a.reason})`).join("; ")}`;
    }
    window._mlAnomalyTitles = d.anomalies.map(a => a.title.toLowerCase());
  } catch(e) {}
}

// ── 6. Duplicate Check ────────────────────────────────────────
async function mlCheckDuplicate(title, amount, transactions) {
  const el = document.getElementById("duplicateWarning");
  if (!el || !title || amount <= 0) return;
  try {
    const res = await fetch(`${ML_BASE}/ml/duplicate-check`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transactions, new_title: title, new_amount: amount })
    });
    if (!res.ok) return;
    const d = await res.json();
    if (d.is_duplicate) {
      el.classList.remove("d-none");
      el.innerHTML = `⚠️ ${d.message} — sure this isn't a duplicate?`;
    } else {
      el.classList.add("d-none");
    }
  } catch(e) { el.classList.add("d-none"); }
}

// ── Auto-wire inputs ──────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const titleInput  = document.getElementById("txnTitle");
  const amountInput = document.getElementById("txnAmount");
  if (titleInput)  titleInput.addEventListener("input",  () => mlPredictCategory(titleInput.value));
  if (amountInput) amountInput.addEventListener("blur", async () => {
    const title  = titleInput?.value?.trim();
    const amount = parseFloat(amountInput.value);
    if (title && amount > 0) {
      const txnData = await fetch("/api/transactions").then(r=>r.json()).catch(()=>({transactions:[]}));
      mlCheckDuplicate(title, amount, txnData.transactions || []);
    }
  });
});
