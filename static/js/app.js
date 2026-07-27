// ---------------------------------------------------------------------
// MedAssist AI - frontend logic
// Talks to the Flask backend at the same origin, so no CORS setup needed.
// ---------------------------------------------------------------------

const state = {
  allSymptoms: [],
  selected: new Set(),
  lastPredictedDisease: null,
  lastSymptoms: [],
};

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
};

// Diseases worth flagging as high-risk in the UI. Extend this list to
// match whatever your dataset considers severe.
const HIGH_RISK_DISEASES = new Set([
  "Heart attack", "Paralysis (brain hemorrhage)", "Tuberculosis", "AIDS", "Pneumonia"
]);

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
      if (e.target.checked) {
        state.selected.add(e.target.value);
      } else {
        state.selected.delete(e.target.value);
      }
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
// 2. Predict
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
    renderResults(data);
    openChatFor(data.top3_predictions[0].disease);
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
      <div class="result-top">
        <span class="result-disease">Why this prediction?</span>
      </div>
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

  el.dtPrediction.closest(".result-card")
    ? el.dtPrediction.parentElement.insertAdjacentHTML("afterend", html)
    : el.top3List.insertAdjacentHTML("afterend", html);
}

function renderResults(data) {
  el.resultsEmpty.classList.add("hidden");
  el.resultsContent.classList.remove("hidden");

  el.top3List.innerHTML = data.top3_predictions
    .map((pred, i) => {
      const highRisk = HIGH_RISK_DISEASES.has(pred.disease);
      return `
        <div class="result-card rank-${i} ${highRisk ? "high-risk" : ""}">
          <div class="result-top">
            <span class="result-disease">${i + 1}. ${pred.disease}</span>
            <span class="result-confidence">${pred.confidence}%</span>
          </div>
          <div class="confidence-bar">
            <div class="confidence-bar-fill" style="width:${pred.confidence}%"></div>
          </div>
          ${highRisk ? '<p style="color:var(--warn);font-size:0.8rem;margin:8px 0 0;font-weight:600;">⚠ High risk — please consult a doctor promptly.</p>' : ""}
        </div>`;
    })
    .join("");

  // el.dtPrediction.textContent = data.decision_tree_prediction;
  el.dtPrediction.textContent = data.decision_tree_prediction;
  renderPredictionReason(data.prediction_reason);

}

// ---------------------------------------------------------------------
// 3. Chat
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

  // addMessage("user", question);
  // el.chatInput.value = "";
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