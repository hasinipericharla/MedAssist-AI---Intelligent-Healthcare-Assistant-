// ---------------------------------------------------------------------
// Account page: edit signup details (name/email), change password,
// demo two-step verification. Separate from profile.js (Health Profile).
// ---------------------------------------------------------------------

const session = MA.getSession();
const nameInput = document.getElementById("ac-name");
const emailInput = document.getElementById("ac-email");

if (session) {
  const user = MA.getUsers().find((u) => u.email === session.email);
  if (user) {
    nameInput.value = user.name;
    emailInput.value = user.email;
  }
}

const editBtn = document.getElementById("editDetailsBtn");
const saveBtn = document.getElementById("saveDetailsBtn");

editBtn.addEventListener("click", () => {
  nameInput.disabled = false;
  emailInput.disabled = false;
  nameInput.focus();
  editBtn.classList.add("hidden");
  saveBtn.classList.remove("hidden");
});

document.getElementById("accountDetailsForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const note = document.getElementById("detailsNote");
  note.style.display = "block";
  if (!session) {
    note.textContent = "You need to be logged in.";
    return;
  }
  const newName = nameInput.value.trim();
  const newEmail = emailInput.value.trim().toLowerCase();

  if (newEmail !== session.email && MA.getUsers().some((u) => u.email === newEmail)) {
    note.textContent = "That email is already in use.";
    return;
  }
  MA.updateUser(session.email, { name: newName, email: newEmail });
  MA.setSession({ name: newName, email: newEmail });
  note.textContent = "Saved.";
  nameInput.disabled = true;
  emailInput.disabled = true;
  saveBtn.classList.add("hidden");
  editBtn.classList.remove("hidden");
  setTimeout(() => location.reload(), 700);
});

document.getElementById("passwordForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const note = document.getElementById("passwordNote");
  note.style.display = "block";
  if (!session) {
    note.textContent = "You need to be logged in to change your password.";
    return;
  }
  const current = document.getElementById("pw-current").value;
  const next = document.getElementById("pw-new").value;
  const confirm = document.getElementById("pw-confirm").value;

  const user = MA.getUsers().find((u) => u.email === session.email);
  if (!user || user.password !== current) {
    note.textContent = "Current password is incorrect.";
    return;
  }
  if (next !== confirm) {
    note.textContent = "New passwords don't match.";
    return;
  }
  MA.updateUser(session.email, { password: next });
  note.textContent = "Password updated.";
  e.target.reset();
});

const twoFAToggle = document.getElementById("twoFAToggle");
const twoFASetup = document.getElementById("twoFASetup");
const twoFANote = document.getElementById("twoFANote");
let pendingCode = null;

if (session) {
  const user = MA.getUsers().find((u) => u.email === session.email);
  twoFAToggle.checked = !!user?.twoFAEnabled;
}

twoFAToggle.addEventListener("change", () => {
  if (!session) return;
  if (twoFAToggle.checked) {
    pendingCode = String(Math.floor(100000 + Math.random() * 900000));
    document.getElementById("twoFADemoCode").textContent = pendingCode;
    twoFASetup.classList.remove("hidden");
  } else {
    MA.updateUser(session.email, { twoFAEnabled: false });
    twoFASetup.classList.add("hidden");
    twoFANote.style.display = "block";
    twoFANote.textContent = "Two-step verification disabled.";
  }
});

document.getElementById("twoFAConfirmBtn").addEventListener("click", () => {
  const entered = document.getElementById("twoFAConfirmInput").value.trim();
  twoFANote.style.display = "block";
  if (entered === pendingCode) {
    MA.updateUser(session.email, { twoFAEnabled: true });
    twoFASetup.classList.add("hidden");
    twoFANote.textContent = "Two-step verification enabled.";
  } else {
    twoFANote.textContent = "Incorrect code — try again.";
    twoFAToggle.checked = false;
  }
});