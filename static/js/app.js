// ---------------------------------------------------------------------
// MedAssist AI - predict page logic
// Modules 1, 2, 4 talk to the REAL Flask backend (/api/predict, /api/chat).
// Modules 5 (health score), 7 (history), 8 (PDF), 10 (voice), 12 (alert)
// are computed/stored client-side via window.MA (see shell.js) since
// there's no backend route for them yet.
// ---------------------------------------------------------------------

const state = {
  allSymptoms: [],
  selected: new Set(),
  lastPredictedDisease: null,
  lastSymptoms: [],
  lastData: null,
};

const HIGH_RISK_DISEASES = new Set([
  "Heart attack", "Paralysis (brain hemorrhage)", "Tuberculosis", "AIDS", "Pneumonia"
]);

const el = {
  search: document.getElementById("symptomSearch"),
  list: document.getElementById("symptomList"),
  chips: document.getElementById("selectedChips"),
  predictBtn: document.getElementById("predictBtn"),
  resultsEmpty: document.getElementById("resultsEmpty"),
  resultsContent: document.getElementById("resultsContent"),
  top3List: document.getElementById("top3List"),
  dtPrediction: document.getElementById("dtPrediction"),
  chatPanel: document.getElementById("chatPanel"),
  chatDiseaseName: document.getElementById("chatDiseaseName"),
  chatMessages: document.getElementById("chatMessages"),
  chatForm: document.getElementById("chatForm"),
  chatInput: document.getElementById("chatInput"),
  voiceBtn: document.getElementById("voiceBtn"),
  voiceStatus: document.getElementById("voiceStatus"),
  emergencyAlert: document.getElementById("emergencyAlert"),
  healthScoreValue: document.getElementById("healthScoreValue"),
  healthRiskBadge: document.getElementById("healthRiskBadge"),
  downloadReportBtn: document.getElementById("downloadReportBtn"),
  feedbackYesBtn: document.getElementById("feedbackYesBtn"),
  feedbackNoBtn: document.getElementById("feedbackNoBtn"),
  feedbackNote: document.getElementById("feedbackNote"),
};

// ---------------------------------------------------------------------
// 1. Load symptom list from /api/symptoms and render it
// ---------------------------------------------------------------------

async function loadSymptoms() {
  try {
    const res = await fetch("/api/symptoms");
    const data = await res.json();
    state.allSymptoms = data.symptoms || [];
    renderSymptomList(state.allSymptoms);
  } catch (err) {
    el.list.innerHTML = `<p class="loading-text">Couldn't load symptoms. Is the server running?</p>`;
  }
}

function prettySymptomName(raw) {
  return raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function renderSymptomList(symptoms) {
  if (symptoms.length === 0) {
    el.list.innerHTML = `<p class="loading-text">No symptoms match your search.</p>`;
    return;
  }
  el.list.innerHTML = symptoms
    .map((s) => {
      const checked = state.selected.has(s) ? "checked" : "";
      return `
        <label class="symptom-item">
          <input type="checkbox" value="${s}" ${checked} />
          <span>${prettySymptomName(s)}</span>
        </label>`;
    })
    .join("");

  el.list.querySelectorAll("input[type=checkbox]").forEach((input) => {
    input.addEventListener("change", (e) => {
      if (e.target.checked) state.selected.add(e.target.value);
      else state.selected.delete(e.target.value);
      renderChips();
      el.predictBtn.disabled = state.selected.size === 0;
    });
  });
}

function renderChips() {
  el.chips.innerHTML = Array.from(state.selected)
    .map(
      (s) => `
      <span class="chip" data-symptom="${s}">
        ${prettySymptomName(s)}
        <button type="button" aria-label="Remove ${prettySymptomName(s)}">&times;</button>
      </span>`
    )
    .join("");

  el.chips.querySelectorAll(".chip button").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const symptom = e.target.closest(".chip").dataset.symptom;
      state.selected.delete(symptom);
      renderChips();
      renderSymptomList(filterSymptoms(el.search.value));
      el.predictBtn.disabled = state.selected.size === 0;
    });
  });
}

function filterSymptoms(query) {
  const q = query.trim().toLowerCase().replace(/\s+/g, "_");
  if (!q) return state.allSymptoms;
  return state.allSymptoms.filter((s) => s.includes(q));
}

el.search.addEventListener("input", () => {
  renderSymptomList(filterSymptoms(el.search.value));
});

// ---------------------------------------------------------------------
// 2. Predict (Module 1) + explainability (Module 4)
// ---------------------------------------------------------------------

el.predictBtn.addEventListener("click", async () => {
  const symptoms = Array.from(state.selected);
  el.predictBtn.disabled = true;
  el.predictBtn.textContent = "Checking…";

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symptoms }),
    });
    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Something went wrong.");
      return;
    }

    state.lastSymptoms = symptoms;
    state.lastData = data;
    renderResults(data);
    openChatFor(data.top3_predictions[0].disease);

    // Module 7: log this run to prediction history (client-side store)
    MA.addHistoryEntry({
      disease: data.top3_predictions[0].disease,
      confidence: data.top3_predictions[0].confidence,
      symptoms,
    });
  } catch (err) {
    alert("Couldn't reach the server. Is app.py running?");
  } finally {
    el.predictBtn.disabled = false;
    el.predictBtn.textContent = "Check my symptoms";
  }
});

function renderPredictionReason(reasons) {
  const existing = document.getElementById("predictionReason");
  if (existing) existing.remove();
  if (!reasons || reasons.length === 0) return;

  const html = `
    <div id="predictionReason" class="result-card" style="margin-top:16px;">
      <div class="result-top"><span class="result-disease">Why this prediction?</span></div>
      ${reasons
        .map(
          (r) => `
        <div style="display:flex;justify-content:space-between;margin-top:8px;">
          <span>✔ ${prettySymptomName(r.symptom)}</span>
          <span>${r.contribution_percent}%</span>
        </div>`
        )
        .join("")}
    </div>`;
  el.top3List.insertAdjacentHTML("afterend", html);
}

function renderResults(data) {
  el.resultsEmpty.classList.add("hidden");
  el.resultsContent.classList.remove("hidden");

  const topDisease = data.top3_predictions[0].disease;
  const highRisk = HIGH_RISK_DISEASES.has(topDisease);
  el.emergencyAlert.classList.toggle("hidden", !highRisk); // Module 12

  el.top3List.innerHTML = data.top3_predictions
    .map((pred, i) => {
      const isHighRisk = HIGH_RISK_DISEASES.has(pred.disease);
      return `
        <div class="result-card rank-${i} ${isHighRisk ? "high-risk" : ""}">
          <div class="result-top">
            <span class="result-disease">${i + 1}. ${pred.disease}</span>
            <span class="result-confidence">${pred.confidence}%</span>
          </div>
          <div class="confidence-bar">
            <div class="confidence-bar-fill" style="width:${pred.confidence}%"></div>
          </div>
          ${isHighRisk ? '<p style="color:var(--warn);font-size:0.8rem;margin:8px 0 0;font-weight:600;">⚠ High risk — please consult a doctor promptly.</p>' : ""}
        </div>`;
    })
    .join("");

  el.dtPrediction.textContent = data.decision_tree_prediction;
  renderPredictionReason(data.prediction_reason);
  renderHealthScore(data); // Module 5
  el.feedbackNote.style.display = "none";
}

// ---------------------------------------------------------------------
// Module 5: Health Risk Score (client-side, uses profile if available)
// ---------------------------------------------------------------------

function renderHealthScore(data) {
  const profile = MA.getProfile();
  const bmi = profile ? MA.computeBMI(profile.heightCm, profile.weightKg) : null;
  const { score, risk } = MA.computeHealthScore({
    bmi,
    symptomCount: state.lastSymptoms.length,
    topConfidence: data.top3_predictions[0].confidence,
  });
  el.healthScoreValue.textContent = `${score}/100`;
  el.healthRiskBadge.textContent = risk;
  el.healthRiskBadge.className = `badge badge-${risk.toLowerCase()}`;
}

// ---------------------------------------------------------------------
// Module 8: PDF Medical Report (client-side via jsPDF)
// ---------------------------------------------------------------------

el.downloadReportBtn.addEventListener("click", () => {
  if (!state.lastData) return;
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();
  const profile = MA.getProfile();
  const top = state.lastData.top3_predictions[0];

  doc.setFontSize(16);
  doc.text("MedAssist AI - Medical Report", 14, 18);
  doc.setFontSize(10);
  doc.text(`Date: ${new Date().toLocaleString()}`, 14, 26);

  doc.setFontSize(12);
  doc.text("Patient Details", 14, 38);
  doc.setFontSize(10);
  doc.text(`Name: ${profile?.name || "Not provided"}`, 14, 45);
  doc.text(`Age: ${profile?.age || "-"}   Gender: ${profile?.gender || "-"}`, 14, 51);
  doc.text(`Height: ${profile?.heightCm || "-"} cm   Weight: ${profile?.weightKg || "-"} kg`, 14, 57);
  doc.text(`Allergies: ${profile?.allergies || "None reported"}`, 14, 63);

  doc.setFontSize(12);
  doc.text("Symptoms Reported", 14, 75);
  doc.setFontSize(10);
  doc.text(state.lastSymptoms.map(prettySymptomName).join(", ") || "None", 14, 82, { maxWidth: 180 });

  doc.setFontSize(12);
  doc.text("Prediction", 14, 96);
  doc.setFontSize(10);
  doc.text(`Top prediction: ${top.disease} (${top.confidence}% confidence)`, 14, 103);
  doc.text(`Decision Tree prediction: ${state.lastData.decision_tree_prediction}`, 14, 109);

  doc.setFontSize(12);
  doc.text("Suggestions", 14, 121);
  doc.setFontSize(10);
  doc.text("Consult a licensed physician to confirm this prediction before taking", 14, 128);
  doc.text("any medication or treatment action.", 14, 134);

  doc.save(`MedAssist-Report-${Date.now()}.pdf`);
});

// ---------------------------------------------------------------------
// AI Feedback Loop (mentioned in spec as the standout feature)
// ---------------------------------------------------------------------

function submitFeedback(helpful) {
  if (!state.lastData) return;
  const list = JSON.parse(localStorage.getItem(MA.KEYS.feedback) || "[]");
  list.unshift({
    disease: state.lastData.top3_predictions[0].disease,
    helpful,
    date: new Date().toISOString(),
  });
  localStorage.setItem(MA.KEYS.feedback, JSON.stringify(list.slice(0, 200)));
  el.feedbackNote.style.display = "block";
}
el.feedbackYesBtn.addEventListener("click", () => submitFeedback(true));
el.feedbackNoBtn.addEventListener("click", () => submitFeedback(false));

// ---------------------------------------------------------------------
// Module 10: Voice input via Web Speech API
// ---------------------------------------------------------------------

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
  const recognizer = new SpeechRecognition();
  recognizer.lang = "en-US";
  recognizer.interimResults = false;

  // el.voiceBtn.addEventListener("click", () => {
  //   el.voiceStatus.style.display = "block";
  //   el.voiceStatus.textContent = "Listening… say something like 'I have fever and headache'";
  //   recognizer.start();
  // });

  // recognizer.addEventListener("result", (e) => {
  //   const transcript = e.results[0][0].transcript;
  //   el.voiceStatus.textContent = `Heard: "${transcript}" — matching symptoms…`;
  //   matchSpokenSymptoms(transcript);
  // });

  // recognizer.addEventListener("error", () => {
  //   el.voiceStatus.textContent = "Couldn't hear that clearly. Try again or type instead.";
  // });
    el.voiceBtn.addEventListener("click", () => {
    el.voiceBtn.classList.add("listening");
    el.voiceStatus.style.display = "block";
    el.voiceStatus.textContent = "Listening… say something like 'I have fever and headache'";
    recognizer.start();
  });

  recognizer.addEventListener("result", (e) => {
    const transcript = e.results[0][0].transcript;
    el.voiceStatus.textContent = `Heard: "${transcript}" — matching symptoms…`;
    matchSpokenSymptoms(transcript);
  });

  recognizer.addEventListener("error", () => {
    el.voiceStatus.textContent = "Couldn't hear that clearly. Try again or type instead.";
  });

  recognizer.addEventListener("end", () => {
    el.voiceBtn.classList.remove("listening");
  });
} else {
  el.voiceBtn.style.display = "none";
}

function matchSpokenSymptoms(transcript) {
  const words = transcript.toLowerCase().replace(/[^a-z\s]/g, "").split(/\s+/);
  const matched = state.allSymptoms.filter((symptom) => {
    const parts = symptom.split("_");
    return parts.every((p) => words.includes(p)) || words.includes(symptom);
  });
  matched.forEach((s) => state.selected.add(s));
  renderChips();
  renderSymptomList(filterSymptoms(el.search.value));
  el.predictBtn.disabled = state.selected.size === 0;
  el.voiceStatus.textContent = matched.length
    ? `Matched: ${matched.map(prettySymptomName).join(", ")}`
    : "No matching symptoms found in that sentence — try selecting manually.";
}

// ---------------------------------------------------------------------
// 3. Chat (Module 2)
// ---------------------------------------------------------------------

function openChatFor(disease) {
  state.lastPredictedDisease = disease;
  el.chatDiseaseName.textContent = disease;
  el.chatPanel.classList.remove("hidden");
  el.chatMessages.innerHTML = "";
  addMessage(
    "assistant",
    `I see your top prediction is ${disease}. Ask me anything about it — foods, activity, medicine, or why it was flagged.`
  );
}

function addMessage(role, text, source) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = `${text}${source ? `<span class="msg-source">${source === "llm" ? "AI-generated" : "reference info"}</span>` : ""}`;
  el.chatMessages.appendChild(div);
  el.chatMessages.scrollTop = el.chatMessages.scrollHeight;
}

el.chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = el.chatInput.value.trim();
  if (!question || !state.lastPredictedDisease) return;

  addMessage("user", question);
  el.chatInput.value = "";
  addMessage("assistant", "Thinking…");
  const thinkingMsg = el.chatMessages.lastElementChild;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        disease: state.lastPredictedDisease,
        question,
        symptoms: state.lastSymptoms,
      }),
    });
    const data = await res.json();

    if (!res.ok) {
      thinkingMsg.remove();
      addMessage("assistant", data.error || "Something went wrong.");
      return;
    }
    thinkingMsg.remove();
    addMessage("assistant", data.answer, data.source);
  } catch (err) {
    thinkingMsg.remove();
    addMessage("assistant", "Couldn't reach the server.");
  }
});

// ---------------------------------------------------------------------
loadSymptoms();
