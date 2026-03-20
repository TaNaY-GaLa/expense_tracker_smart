/**
 * heatmap.js — Visual Analytics Features (Phase 2)
 * - Spending Heatmap Calendar
 * - Day-of-Week Pattern Chart
 * - Spending vs Last Month Comparison
 */

// ══════════════════════════════════════════════════════
// 1. SPENDING HEATMAP CALENDAR (GitHub-style)
// ══════════════════════════════════════════════════════
function renderHeatmap(transactions) {
  const container = document.getElementById("heatmapContainer");
  if (!container) return;

  // Build date→amount map
  const dayMap = {};
  transactions.forEach(t => {
    dayMap[t.date] = (dayMap[t.date] || 0) + (t.amount_inr || t.amount || 0);
  });

  if (!Object.keys(dayMap).length) {
    container.innerHTML = `<p class="text-muted text-center py-3">No expense data for heatmap yet.</p>`;
    return;
  }

  const maxAmt = Math.max(...Object.values(dayMap));
  const today = new Date();
  const startDate = new Date(today);
  startDate.setDate(startDate.getDate() - 364);

  // Color intensity
  function getColor(amount) {
    if (!amount) return "#f0e6d3";
    const pct = amount / maxAmt;
    if (pct > 0.75) return "#6B4226";
    if (pct > 0.5)  return "#9B6644";
    if (pct > 0.25) return "#C49A6C";
    return "#DFC09A";
  }

  // Build weeks
  const weeks = [];
  let cur = new Date(startDate);
  cur.setDate(cur.getDate() - cur.getDay()); // start from Sunday

  while (cur <= today) {
    const week = [];
    for (let d = 0; d < 7; d++) {
      const dateStr = cur.toISOString().split("T")[0];
      const amt = dayMap[dateStr] || 0;
      week.push({ date: dateStr, amount: amt, inFuture: cur > today });
      cur.setDate(cur.getDate() + 1);
    }
    weeks.push(week);
  }

  const dayLabels = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
  const monthsShown = new Set();

  let html = `<div class="heatmap-wrapper">
    <div class="heatmap-day-labels">
      ${[1,3,5].map(i=>`<div class="heatmap-day-label">${dayLabels[i]}</div>`).join("")}
    </div>
    <div class="heatmap-grid-wrapper">
      <div class="heatmap-grid">`;

  weeks.forEach((week, wi) => {
    html += `<div class="heatmap-week">`;
    week.forEach(day => {
      const tooltip = day.amount > 0
        ? `${day.date}: ₹${day.amount.toLocaleString("en-IN")}`
        : day.date;
      const opacity = day.inFuture ? "opacity:0.3" : "";
      html += `<div class="heatmap-cell" style="background:${getColor(day.amount)};${opacity}" title="${tooltip}" data-date="${day.date}" data-amount="${day.amount}"></div>`;
    });
    html += `</div>`;
  });

  html += `</div></div>`;

  // Legend
  html += `<div class="heatmap-legend mt-2">
    <small class="text-muted me-2">Less</small>
    ${["#f0e6d3","#DFC09A","#C49A6C","#9B6644","#6B4226"].map(c=>`<div class="heatmap-cell" style="background:${c};display:inline-block"></div>`).join("")}
    <small class="text-muted ms-2">More</small>
  </div>`;

  html += `</div>`;
  container.innerHTML = html;
}

// ══════════════════════════════════════════════════════
// 2. DAY-OF-WEEK PATTERN
// ══════════════════════════════════════════════════════
function renderDayOfWeekChart(transactions) {
  const ctx = document.getElementById("dayOfWeekChart");
  if (!ctx) return;

  const days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
  const dayTotals = new Array(7).fill(0);
  const dayCounts = new Array(7).fill(0);

  transactions.forEach(t => {
    const dow = new Date(t.date + "T12:00:00").getDay();
    dayTotals[dow] += t.amount_inr || t.amount || 0;
    dayCounts[dow]++;
  });

  const dayAvgs = dayTotals.map((total, i) => dayCounts[i] > 0 ? Math.round(total / dayCounts[i]) : 0);
  const maxAvg = Math.max(...dayAvgs);

  if (window.dayOfWeekChartInstance) window.dayOfWeekChartInstance.destroy();

  window.dayOfWeekChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: days.map(d => d.slice(0,3)),
      datasets: [{
        label: "Avg Spend (₹)",
        data: dayAvgs,
        backgroundColor: dayAvgs.map(v => v === maxAvg ? "#6B4226" : "rgba(212,169,106,0.6)"),
        borderColor: dayAvgs.map(v => v === maxAvg ? "#3E1F00" : "#D4A96A"),
        borderWidth: 1.5,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => `Avg: ₹${ctx.raw.toLocaleString("en-IN")}`
          }
        }
      },
      scales: {
        y: { ticks: { callback: v => "₹" + v.toLocaleString("en-IN") }, grid: { color: "rgba(0,0,0,0.05)" } },
        x: { grid: { display: false } }
      }
    }
  });

  // Show insight below chart
  const insight = document.getElementById("dowInsight");
  if (insight && maxAvg > 0) {
    const peakDay = days[dayAvgs.indexOf(maxAvg)];
    const minAvg = Math.min(...dayAvgs.filter(v => v > 0));
    const ratio = minAvg > 0 ? (maxAvg / minAvg).toFixed(1) : "—";
    insight.innerHTML = `📊 You spend the most on <strong>${peakDay}s</strong> (avg ₹${maxAvg.toLocaleString("en-IN")}), which is <strong>${ratio}x</strong> more than your lowest spending day.`;
    insight.classList.remove("d-none");
  }
}

// ══════════════════════════════════════════════════════
// 3. SPENDING vs LAST MONTH
// ══════════════════════════════════════════════════════
function renderVsLastMonth(transactions) {
  const ctx = document.getElementById("vsLastMonthChart");
  const statsEl = document.getElementById("vsLastMonthStats");
  if (!ctx) return;

  const now = new Date();
  const thisMonth = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}`;
  const lastMonthDate = new Date(now.getFullYear(), now.getMonth()-1, 1);
  const lastMonth = `${lastMonthDate.getFullYear()}-${String(lastMonthDate.getMonth()+1).padStart(2,"0")}`;

  const thisData = {}, lastData = {};
  const categories = ["Food","Clothing","Travel","Books","Entertainment","Health","Other"];
  categories.forEach(c => { thisData[c] = 0; lastData[c] = 0; });

  transactions.forEach(t => {
    const m = t.date.slice(0,7);
    const cat = categories.includes(t.category) ? t.category : "Other";
    if (m === thisMonth) thisData[cat] += t.amount_inr || t.amount || 0;
    if (m === lastMonth) lastData[cat] += t.amount_inr || t.amount || 0;
  });

  // Filter only categories that have data in either month
  const activeCats = categories.filter(c => thisData[c] > 0 || lastData[c] > 0);
  if (!activeCats.length) return;

  if (window.vsLastMonthChartInstance) window.vsLastMonthChartInstance.destroy();

  const thisMonthName = now.toLocaleString("default",{month:"short",year:"numeric"});
  const lastMonthName = lastMonthDate.toLocaleString("default",{month:"short",year:"numeric"});

  window.vsLastMonthChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: activeCats,
      datasets: [
        {
          label: lastMonthName,
          data: activeCats.map(c => Math.round(lastData[c])),
          backgroundColor: "rgba(212,169,106,0.5)",
          borderColor: "#D4A96A",
          borderWidth: 1.5,
          borderRadius: 4
        },
        {
          label: thisMonthName,
          data: activeCats.map(c => Math.round(thisData[c])),
          backgroundColor: "rgba(107,66,38,0.75)",
          borderColor: "#6B4226",
          borderWidth: 1.5,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "top" },
        tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ₹${ctx.raw.toLocaleString("en-IN")}` } }
      },
      scales: {
        y: { ticks: { callback: v => "₹"+v.toLocaleString("en-IN") }, grid: { color: "rgba(0,0,0,0.05)" } },
        x: { grid: { display: false } }
      }
    }
  });

  // Stats summary
  if (statsEl) {
    const thisTotal = Object.values(thisData).reduce((a,b)=>a+b,0);
    const lastTotal = Object.values(lastData).reduce((a,b)=>a+b,0);
    if (lastTotal > 0) {
      const diff = thisTotal - lastTotal;
      const pct = Math.abs((diff/lastTotal)*100).toFixed(1);
      const up = diff > 0;
      statsEl.innerHTML = `You spent <strong>₹${Math.abs(diff).toLocaleString("en-IN")} (${pct}%) ${up?"more":"less"}</strong> this month compared to last month ${up?"📈":"📉"}`;
      statsEl.className = `alert border-0 rounded-3 py-2 px-3 ${up?"alert-warning":"alert-success"}`;
      statsEl.classList.remove("d-none");
    }
  }
}

// ── Init all visual features ───────────────────────────────
async function initVisualFeatures() {
  try {
    const res = await fetch("/api/transactions");
    const data = await res.json();
    const txns = data.transactions || [];

    // Add amount_inr fallback
    txns.forEach(t => { if (!t.amount_inr) t.amount_inr = t.amount; });

    renderHeatmap(txns);
    renderDayOfWeekChart(txns);
    renderVsLastMonth(txns);
  } catch (e) {
    console.error("Visual features error:", e);
  }
}

document.addEventListener("DOMContentLoaded", initVisualFeatures);
