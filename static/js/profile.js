// ---------------------------------------------------------------------
// Module 3: Personalized Health Profile
// Stored via MA.saveProfile/getProfile (localStorage) until a real
// /api/profile route exists. Swap loadProfile/saveProfile bodies for
// fetch() calls then -- the form logic below won't need to change.
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

function loadProfile() {
  const p = MA.getProfile();
  if (!p) return;
  fields.name.value = p.name || "";
  fields.age.value = p.age || "";
  fields.gender.value = p.gender || "";
  fields.height.value = p.heightCm || "";
  fields.weight.value = p.weightKg || "";
  fields.history.value = p.history || "";
  fields.allergies.value = p.allergies || "";
  updateBMI();
  updatePreview(p);
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

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const profile = {
    name: fields.name.value.trim(),
    age: fields.age.value ? Number(fields.age.value) : null,
    gender: fields.gender.value,
    heightCm: fields.height.value ? Number(fields.height.value) : null,
    weightKg: fields.weight.value ? Number(fields.weight.value) : null,
    history: fields.history.value.trim(),
    allergies: fields.allergies.value.trim(),
  };
  MA.saveProfile(profile);
  updatePreview(profile);
  savedNote.style.display = "inline";
  setTimeout(() => (savedNote.style.display = "none"), 2500);
});

loadProfile();