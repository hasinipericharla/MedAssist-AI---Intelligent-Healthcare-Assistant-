// ---------------------------------------------------------------------
// Module 3: Personalized Health Profile
// Backed by MongoDB via /api/profile (GET to load, POST to save), keyed
// to the logged-in user's email from MA.getSession(). Form logic is the
// same as before -- only loadProfile/save now hit the real backend
// instead of localStorage.
// ---------------------------------------------------------------------

const fields = {
  name: document.getElementById("pf-name"),
  age: document.getElementById("pf-age"),
  gender: document.getElementById("pf-gender"),
  height: document.getElementById("pf-height"),
  weight: document.getElementById("pf-weight"),
  bmi: document.getElementById("pf-bmi"),
  history: document.getElementById("pf-history"),
  allergies: document.getElementById("pf-allergies"),
};
const form = document.getElementById("profileForm");
const savedNote = document.getElementById("profileSavedNote");
const preview = document.getElementById("recommendationPreview");

function currentEmail() {
  const session = MA.getSession();
  return session ? session.email : null;
}

async function loadProfile() {
  const email = currentEmail();
  if (!email) return; // not logged in -- shell.js should already be redirecting

  let profile;
  try {
    const res = await fetch(`/api/profile?email=${encodeURIComponent(email)}`);
    if (!res.ok) throw new Error("Could not load profile");
    profile = await res.json();
  } catch (err) {
    console.error(err);
    return;
  }

  fields.name.value = profile.name || "";
  fields.age.value = profile.age || "";
  fields.gender.value = profile.gender || "";
  fields.height.value = profile.heightCm || "";
  fields.weight.value = profile.weightKg || "";
  fields.history.value = profile.history || "";
  fields.allergies.value = profile.allergies || "";
  updateBMI();
  updatePreview(profile);
}

function updateBMI() {
  const bmi = MA.computeBMI(Number(fields.height.value), Number(fields.weight.value));
  fields.bmi.value = bmi ? `${bmi}` : "";
  return bmi;
}

function updatePreview(profile) {
  const bmi = MA.computeBMI(Number(profile.heightCm), Number(profile.weightKg));
  if (!bmi || !profile.age) {
    preview.textContent = "Fill in your profile to see a personalized recommendation preview.";
    return;
  }
  let category = "a healthy range";
  let tip = "Keep up your current hydration and activity levels.";
  if (bmi < 18.5) {
    category = "the underweight range";
    tip = "Consider nutrient-dense meals and check in with a doctor about healthy weight gain.";
  } else if (bmi >= 25 && bmi < 30) {
    category = "the overweight range";
    tip = "Increase hydration, favor lighter meals, and avoid cold drinks after meals.";
  } else if (bmi >= 30) {
    category = "the obese range";
    tip = "Based on your BMI and age, prioritize hydration, avoid cold drinks, and consult a doctor about a tailored plan.";
  }
  preview.innerHTML = `<strong>BMI ${bmi}</strong> puts you in ${category} for someone aged ${profile.age}. ${tip}`;
}

[fields.height, fields.weight].forEach((f) => f.addEventListener("input", updateBMI));

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = currentEmail();
  if (!email) return;

  const profile = {
    email,
    name: fields.name.value.trim(),
    age: fields.age.value ? Number(fields.age.value) : null,
    gender: fields.gender.value,
    heightCm: fields.height.value ? Number(fields.height.value) : null,
    weightKg: fields.weight.value ? Number(fields.weight.value) : null,
    history: fields.history.value.trim(),
    allergies: fields.allergies.value.trim(),
  };

  try {
    const res = await fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    if (!res.ok) throw new Error("Save failed");
    updatePreview(profile);
    savedNote.style.display = "inline";
    setTimeout(() => (savedNote.style.display = "none"), 2500);
  } catch (err) {
    console.error(err);
    alert("Could not save your profile. Please try again.");
  }
});

loadProfile();