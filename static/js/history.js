// ---------------------------------------------------------------------
// Module 7: Prediction History
// Reads from MA.getHistory() (localStorage), written to by app.js every
// time a prediction runs. Swap for a fetch("/api/history") call once
// you add a real endpoint + persist predictions server-side.
// ---------------------------------------------------------------------

const body = document.getElementById("historyBody");
const emptyBlock = document.getElementById("historyEmpty");
const filterInput = document.getElementById("historyFilter");

function prettySymptom(raw) {
  return raw.replace(/_/g, " ");
}

function render(list) {
  if (list.length === 0) {
    body.innerHTML = "";
    emptyBlock.classList.remove("hidden");
    return;
  }
  emptyBlock.classList.add("hidden");
  body.innerHTML = list
    .map(
      (entry) => `
      <tr>
        <td>${new Date(entry.date).toLocaleString()}</td>
        <td>${entry.disease}</td>
        <td>${entry.confidence}%</td>
        <td>${entry.symptoms.map(prettySymptom).join(", ")}</td>
      </tr>`
    )
    .join("");
}

function currentFiltered() {
  const q = filterInput.value.trim().toLowerCase();
  const all = MA.getHistory();
  if (!q) return all;
  return all.filter((e) => e.disease.toLowerCase().includes(q));
}

filterInput.addEventListener("input", () => render(currentFiltered()));

document.getElementById("clearHistoryBtn").addEventListener("click", () => {
  if (!confirm("Clear all prediction history on this device?")) return;
  MA.clearHistory();
  render([]);
});

document.getElementById("downloadHistoryBtn").addEventListener("click", () => {
  const list = MA.getHistory();
  const rows = [["Date", "Disease", "Confidence", "Symptoms"]].concat(
    list.map((e) => [new Date(e.date).toLocaleString(), e.disease, `${e.confidence}%`, e.symptoms.join("; ")])
  );
  const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `medassist-history-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
});

render(currentFiltered());
