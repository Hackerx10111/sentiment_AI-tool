/* ─── State ────────────────────────────────────────────────────────────────── */
let allReviews = [];
let currentFilter = "all";
let barChart = null, pieChart = null, trendChart = null;
let trendData = { labels: [], pos: [], neg: [], neu: [] };
let batchNum = 0;

const SAMPLE_REVIEWS = [
  "The delivery was super fast and the product quality exceeded my expectations!",
  "Absolutely terrible customer service. Waited 3 weeks and still no response.",
  "The item arrived on time. Nothing special but does what it says.",
  "I love this product! Best purchase I've made this year.",
  "Very disappointed. The product broke after two days of use.",
  "Shipping was okay, product is decent. Not amazing, not bad.",
  "Fantastic! The support team resolved my issue within minutes.",
  "The packaging was damaged and half the contents were missing.",
  "Average experience. Would consider buying again if there was a discount.",
  "Outstanding quality and the price is very reasonable. Highly recommended!",
  "Worst online shopping experience I've ever had. Will never buy here again.",
  "Product is fine. Took a bit longer to arrive than expected.",
  "Exceeded all my expectations — will definitely order again!",
  "The colour was completely different from the photos. Very misleading.",
  "Pretty standard product. Works as described, nothing more."
];

/* ─── Tab switching ────────────────────────────────────────────────────────── */
function switchTab(t) {
  ["paste", "upload"].forEach(id => {
    document.getElementById("tab-" + id).classList.toggle("active", id === t);
    document.getElementById("tab-" + id).setAttribute("aria-selected", id === t);
    document.getElementById("pane-" + id).style.display = id === t ? "block" : "none";
  });
}

function switchViz(v) {
  ["bar", "pie", "trend"].forEach(id => {
    document.getElementById("vt-" + id).classList.toggle("active", id === v);
    document.getElementById("viz-" + id).style.display = id === v ? "block" : "none";
  });
}

/* ─── Single review ────────────────────────────────────────────────────────── */
function clearSingle() {
  document.getElementById("single-input").value = "";
  document.getElementById("single-result").innerHTML = "";
}

async function analyseSingle() {
  const text = document.getElementById("single-input").value.trim();
  if (!text) return;

  const resultEl = document.getElementById("single-result");
  resultEl.innerHTML = `<span class="status-msg"><span class="spinner">⏳</span> Analysing…</span>`;

  try {
    const data = await postJSON("/api/analyse", { reviews: [text] });
    const r = data.results[0];
    addReviews([r]);
    const cls = sentimentClass(r.sentiment);
    const emoji = r.sentiment === "Positive" ? "😊" : r.sentiment === "Negative" ? "😠" : "😐";
    resultEl.innerHTML = `
      <div class="badge badge-${cls}">
        ${emoji} ${r.sentiment} &mdash; ${r.confidence}% confidence
      </div>
      <div class="confidence">Compound score: ${r.scores.compound ?? "—"}</div>
      <div class="reason">Model: ${r.model}</div>`;
  } catch (e) {
    resultEl.innerHTML = `<span style="color:#c0392b;font-size:13px">⚠ Error: ${e.message}</span>`;
  }
}

/* ─── Bulk analysis ────────────────────────────────────────────────────────── */
function loadSample() {
  document.getElementById("bulk-input").value = SAMPLE_REVIEWS.join("\n");
  switchTab("paste");
}

async function analyseBulk() {
  const lines = document.getElementById("bulk-input").value
    .split("\n").map(l => l.trim()).filter(Boolean);
  if (!lines.length) return alert("Please enter at least one review.");

  setStatus(`<span class="spinner">⏳</span> Analysing ${lines.length} review(s)…`);

  try {
    const data = await postJSON("/api/analyse", { reviews: lines });
    addReviews(data.results);
    showInsight(data.summary);
    setStatus("");
  } catch (e) {
    setStatus(`⚠ Error: ${e.message}`);
  }
}

/* ─── CSV upload ───────────────────────────────────────────────────────────── */
function handleDrop(e) {
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
}

function handleCSV(input) {
  if (input.files[0]) uploadFile(input.files[0]);
}

async function uploadFile(file) {
  setStatus(`<span class="spinner">⏳</span> Uploading and analysing "${file.name}"…`);
  const form = new FormData();
  form.append("file", file);

  try {
    const res = await fetch("/api/upload", { method: "POST", body: form });
    if (!res.ok) throw new Error((await res.json()).error || "Upload failed");
    const data = await res.json();
    addReviews(data.results);
    showInsight(data.summary);
    setStatus(`✅ Loaded ${data.results.length} reviews from "${file.name}"`);
  } catch (e) {
    setStatus(`⚠ Error: ${e.message}`);
  }
}

/* ─── Data management ──────────────────────────────────────────────────────── */
function addReviews(results) {
  allReviews.push(...results);

  // Update trend snapshot
  batchNum++;
  trendData.labels.push(`Batch ${batchNum}`);
  trendData.pos.push(allReviews.filter(r => r.sentiment === "Positive").length);
  trendData.neg.push(allReviews.filter(r => r.sentiment === "Negative").length);
  trendData.neu.push(allReviews.filter(r => r.sentiment === "Neutral").length);

  // Detect model in use
  const model = results[0]?.model || "VADER";
  document.getElementById("model-badge").textContent = `Model: ${model}`;

  updateMetrics();
  renderList();
  updateCharts();

  document.getElementById("charts-section").style.display = "block";
  document.getElementById("list-section").style.display = "block";
  document.getElementById("btn-report").style.display = "inline-flex";
}

function clearAll() {
  allReviews = [];
  trendData = { labels: [], pos: [], neg: [], neu: [] };
  batchNum = 0;
  updateMetrics();
  renderList();
  if (barChart) { barChart.destroy(); barChart = null; }
  if (pieChart) { pieChart.destroy(); pieChart = null; }
  if (trendChart) { trendChart.destroy(); trendChart = null; }
  document.getElementById("charts-section").style.display = "none";
  document.getElementById("list-section").style.display = "none";
  document.getElementById("btn-report").style.display = "none";
  document.getElementById("insight-box").style.display = "none";
}

/* ─── Metrics ──────────────────────────────────────────────────────────────── */
function updateMetrics() {
  const pos = allReviews.filter(r => r.sentiment === "Positive").length;
  const neg = allReviews.filter(r => r.sentiment === "Negative").length;
  const neu = allReviews.filter(r => r.sentiment === "Neutral").length;
  document.getElementById("cnt-pos").textContent = pos;
  document.getElementById("cnt-neg").textContent = neg;
  document.getElementById("cnt-neu").textContent = neu;
  document.getElementById("cnt-total").textContent = allReviews.length;
}

/* ─── Review list ──────────────────────────────────────────────────────────── */
function filterList(f) {
  currentFilter = f;
  ["all", "Positive", "Negative", "Neutral"].forEach(id => {
    const el = document.getElementById("f-" + (id === "all" ? "all" : id.toLowerCase().slice(0, 3)));
    if (el) el.classList.toggle("active", id === f);
  });
  renderList();
}

function renderList() {
  const filtered = currentFilter === "all"
    ? allReviews
    : allReviews.filter(r => r.sentiment === currentFilter);

  document.getElementById("list-count").textContent = `(${filtered.length})`;

  document.getElementById("reviews-list").innerHTML = filtered.map(r => {
    const cls = sentimentClass(r.sentiment);
    const emoji = r.sentiment === "Positive" ? "😊" : r.sentiment === "Negative" ? "😠" : "😐";
    return `
      <div class="review-item" role="listitem">
        <span class="review-text">${escHtml(r.text)}</span>
        <div class="review-meta">
          <span class="pill pill-${cls}">${emoji} ${r.sentiment}</span>
          <span class="conf-pct">${r.confidence}% confident</span>
        </div>
      </div>`;
  }).join("");
}

/* ─── Charts ───────────────────────────────────────────────────────────────── */
const COLORS = { Positive: "#1D9E75", Negative: "#D85A30", Neutral: "#BA7517" };

function updateCharts() {
  const pos = allReviews.filter(r => r.sentiment === "Positive").length;
  const neg = allReviews.filter(r => r.sentiment === "Negative").length;
  const neu = allReviews.filter(r => r.sentiment === "Neutral").length;
  const total = pos + neg + neu || 1;

  const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 400 }
  };

  /* Bar chart */
  if (barChart) {
    barChart.data.datasets[0].data = [pos, neg, neu];
    barChart.update();
  } else {
    barChart = new Chart(document.getElementById("barChart"), {
      type: "bar",
      data: {
        labels: ["Positive", "Negative", "Neutral"],
        datasets: [{
          label: "Reviews",
          data: [pos, neg, neu],
          backgroundColor: ["#1D9E75", "#D85A30", "#BA7517"],
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        ...chartDefaults,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => `${c.raw} reviews (${Math.round(c.raw / total * 100)}%)` } }
        },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: "rgba(0,0,0,.06)" } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  /* Pie / Doughnut chart */
  if (pieChart) {
    pieChart.data.datasets[0].data = [pos, neg, neu];
    pieChart.update();
  } else {
    pieChart = new Chart(document.getElementById("pieChart"), {
      type: "doughnut",
      data: {
        labels: ["Positive", "Negative", "Neutral"],
        datasets: [{
          data: [pos, neg, neu],
          backgroundColor: ["#1D9E75", "#D85A30", "#BA7517"],
          borderWidth: 2,
          borderColor: "#fff",
          hoverOffset: 8
        }]
      },
      options: {
        ...chartDefaults,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => `${c.label}: ${Math.round(c.raw / total * 100)}%` } }
        },
        cutout: "58%"
      }
    });
  }

  /* Trend line chart */
  if (trendChart) {
    trendChart.data.labels = trendData.labels;
    trendChart.data.datasets[0].data = trendData.pos;
    trendChart.data.datasets[1].data = trendData.neg;
    trendChart.data.datasets[2].data = trendData.neu;
    trendChart.update();
  } else {
    trendChart = new Chart(document.getElementById("trendChart"), {
      type: "line",
      data: {
        labels: trendData.labels,
        datasets: [
          { label: "Positive", data: trendData.pos, borderColor: "#1D9E75", backgroundColor: "rgba(29,158,117,.1)", tension: .4, fill: true, pointRadius: 5 },
          { label: "Negative", data: trendData.neg, borderColor: "#D85A30", backgroundColor: "rgba(216,90,48,.08)", tension: .4, fill: true, pointRadius: 5, borderDash: [5, 3] },
          { label: "Neutral",  data: trendData.neu, borderColor: "#BA7517", backgroundColor: "rgba(186,117,23,.08)", tension: .4, fill: true, pointRadius: 5, borderDash: [2, 4] }
        ]
      },
      options: {
        ...chartDefaults,
        plugins: { legend: { position: "top" } },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: "rgba(0,0,0,.06)" } },
          x: { grid: { display: false } }
        }
      }
    });
  }
}

/* ─── Insight box ──────────────────────────────────────────────────────────── */
function showInsight(summary) {
  const { total, percentages, dominant, counts } = summary;
  const tone = percentages.Positive > 60
    ? "Overall sentiment is <strong>positive</strong> 😊 — customers are satisfied."
    : percentages.Negative > 40
    ? "Overall sentiment is <strong>concerning</strong> 😠 — a high proportion of negative reviews detected."
    : "Sentiment is <strong>mixed</strong> 😐 — no single emotion dominates.";

  const el = document.getElementById("insight-box");
  el.style.display = "block";
  el.innerHTML = `
    <strong>📊 Key Insight:</strong> ${tone}<br>
    Out of <strong>${total}</strong> reviews analysed:
    <strong>${percentages.Positive}%</strong> positive,
    <strong>${percentages.Negative}%</strong> negative,
    <strong>${percentages.Neutral}%</strong> neutral.<br>
    ${counts.Negative > 0
      ? "💡 Tip: Review negative feedback to identify common pain points and improve customer experience."
      : "✅ Keep up the great work — customers are happy!"}`;
}

/* ─── Helpers ──────────────────────────────────────────────────────────────── */
function sentimentClass(s) {
  return s === "Positive" ? "pos" : s === "Negative" ? "neg" : "neu";
}

function escHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function setStatus(html) {
  const el = document.getElementById("bulk-status");
  el.style.display = html ? "block" : "none";
  el.innerHTML = html;
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ─── PDF Report download ──────────────────────────────────────────────────── */
async function downloadReport() {
  if (!allReviews.length) return alert("No reviews analysed yet.");

  const btn = document.getElementById("btn-report");
  btn.disabled = true;
  btn.textContent = "⏳ Generating PDF…";

  const summary = buildSummaryLocally();

  try {
    const res = await fetch("/api/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ results: allReviews, summary }),
    });

    if (!res.ok) throw new Error("Report generation failed");

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `sentiment_report_${new Date().toISOString().slice(0,10)}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert("Error generating report: " + e.message);
  }

  btn.disabled = false;
  btn.textContent = "⬇ Download PDF Report";
}

function buildSummaryLocally() {
  const total = allReviews.length;
  const counts = { Positive: 0, Negative: 0, Neutral: 0 };
  allReviews.forEach(r => { if (counts[r.sentiment] !== undefined) counts[r.sentiment]++; });
  const percentages = {};
  Object.keys(counts).forEach(k => percentages[k] = +(counts[k] / (total || 1) * 100).toFixed(1));
  const dominant = Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b);
  return { total, counts, percentages, dominant };
}


document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("single-input").addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") analyseSingle();
  });
  document.getElementById("bulk-input").addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") analyseBulk();
  });
});
