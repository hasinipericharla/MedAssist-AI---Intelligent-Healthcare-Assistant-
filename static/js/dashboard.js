// ---------------------------------------------------------------------
// Module 6: Health Analytics Dashboard
// Built entirely from MA.getHistory() -- real data accumulated from
// actual predictions run on this device (not mocked). The "model
// accuracy" stat card is the one static number, from your offline
// Module 1 evaluation -- point it at a live metrics endpoint later.
// ---------------------------------------------------------------------

const ACCENT = "#2F9E8F";
const ACCENT_SOFT = "#DCF0EC";
const DEEP = "#123C3C";
const WARN = "#E2673A";

// const ACCENT = "#8B6FB5";
// const ACCENT_SOFT = "#DCD3E8";
// const DEEP = "#4A3B6B";
// const WARN = "#E2673A";

const history = MA.getHistory();

if (history.length === 0) {
  document.getElementById("dashboardEmpty").classList.remove("hidden");
} else {
  renderStats();
  renderDiseaseChart();
  renderSymptomChart();
  renderTrendChart();
}

function renderStats() {
  document.getElementById("statTotal").textContent = history.length;

  const avgConfidence = (
    history.reduce((sum, e) => sum + e.confidence, 0) / history.length
  ).toFixed(1);
  document.getElementById("statAvgConfidence").textContent = `${avgConfidence}%`;

  const counts = {};
  history.forEach((e) => (counts[e.disease] = (counts[e.disease] || 0) + 1));
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  document.getElementById("statTopDisease").textContent = top ? top[0] : "—";
}

function renderDiseaseChart() {
  const counts = {};
  history.forEach((e) => (counts[e.disease] = (counts[e.disease] || 0) + 1));
  const labels = Object.keys(counts);
  const data = Object.values(counts);

  new Chart(document.getElementById("diseaseChart"), {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data, backgroundColor: labels.map((_, i) => (i === 0 ? ACCENT : shade(i))) }],
    },
    options: { plugins: { legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } } } },
  });
}

function renderSymptomChart() {
  const counts = {};
  history.forEach((e) => e.symptoms.forEach((s) => (counts[s] = (counts[s] || 0) + 1)));
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8);

  new Chart(document.getElementById("symptomChart"), {
    type: "bar",
    data: {
      labels: sorted.map(([s]) => s.replace(/_/g, " ")),
      datasets: [{ data: sorted.map(([, c]) => c), backgroundColor: ACCENT }],
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: { x: { ticks: { precision: 0 } } },
    },
  });
}

function renderTrendChart() {
  // Bucket by day for the last 7 days that have data.
  const byDay = {};
  history.forEach((e) => {
    const day = new Date(e.date).toLocaleDateString(undefined, { month: "short", day: "numeric" });
    byDay[day] = (byDay[day] || 0) + 1;
  });
  const days = Object.keys(byDay).slice(-7);

  new Chart(document.getElementById("trendChart"), {
    type: "line",
    data: {
      labels: days,
      datasets: [
        {
          label: "Predictions",
          data: days.map((d) => byDay[d]),
          borderColor: ACCENT,
          backgroundColor: ACCENT_SOFT,
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { precision: 0 } } } },
  });
}

function shade(i) {
  const palette = [ACCENT, DEEP, WARN, "#7FB8AE", "#8A6116", "#B7CFC9"];
  return palette[i % palette.length];
}
