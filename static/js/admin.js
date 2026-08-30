// ---------------------------------------------------------------------
// Module 14: Admin Dashboard
// Reads whatever is in THIS browser's localStorage (users signed up
// here via auth.js, predictions logged here via app.js). This is a UI
// shell -- a real admin view needs a backend with a database so it can
// aggregate data across every user's device, not just the admin's own.
// ---------------------------------------------------------------------

const users = JSON.parse(localStorage.getItem("ma_users") || "[]");
const history = MA.getHistory();
const feedback = JSON.parse(localStorage.getItem(MA.KEYS.feedback) || "[]");

document.getElementById("adminUserCount").textContent = users.length;
document.getElementById("adminPredictionCount").textContent = history.length;
document.getElementById("adminFeedbackCount").textContent = feedback.length;

const userBody = document.getElementById("adminUserBody");
if (users.length === 0) {
  document.getElementById("adminUserEmpty").classList.remove("hidden");
} else {
  userBody.innerHTML = users
    .map((u) => `<tr><td>${u.name}</td><td>${u.email}</td><td>${new Date(u.joined).toLocaleDateString()}</td></tr>`)
    .join("");
}

const predBody = document.getElementById("adminPredictionBody");
if (history.length === 0) {
  document.getElementById("adminPredictionEmpty").classList.remove("hidden");
} else {
  predBody.innerHTML = history
    .slice(0, 50)
    .map((e) => `<tr><td>${new Date(e.date).toLocaleString()}</td><td>${e.disease}</td><td>${e.confidence}%</td></tr>`)
    .join("");
}

document.getElementById("adminDownloadBtn").addEventListener("click", () => {
  const rows = [["Date", "Disease", "Confidence", "Symptoms"]].concat(
    history.map((e) => [new Date(e.date).toLocaleString(), e.disease, `${e.confidence}%`, e.symptoms.join("; ")])
  );
  const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `medassist-admin-predictions-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById("adminLogoutBtn").addEventListener("click", () => {
  localStorage.removeItem("ma_admin_session");
  window.location.href = "/admin-login";
});