// ---------------------------------------------------------------------
// Module 13: Authentication
// Fake login/signup backed by localStorage under "ma_users" + a session
// under MA.KEYS.session. This is NOT secure and is only meant to let
// the rest of the app (nav "signed in" state, admin page) function
// before your real JWT-based /api/auth/* routes exist. Passwords here
// are stored in plain text in the browser -- never do this for real
// auth; when you build the backend, delete fakeLogin/fakeSignup
// entirely and call your API instead.
// ---------------------------------------------------------------------

const USERS_KEY = "ma_users";
const authError = document.getElementById("authError");

function getUsers() {
  return JSON.parse(localStorage.getItem(USERS_KEY) || "[]");
}
function saveUsers(list) {
  localStorage.setItem(USERS_KEY, JSON.stringify(list));
}

function showError(msg) {
  authError.textContent = msg;
  authError.style.display = "block";
}

// Tab switching between the Login and Sign up forms.
const tabs = document.querySelectorAll(".auth-tab");
const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
if (tabs.length) {
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      authError.style.display = "none";
      if (tab.dataset.tab === "login") {
        loginForm.classList.remove("hidden");
        signupForm.classList.add("hidden");
      } else {
        signupForm.classList.remove("hidden");
        loginForm.classList.add("hidden");
      }
    });
  });
}

// If someone who's already logged in lands back on the login page,
// send them straight into the app instead of showing the form again.
if (MA.getSession() && window.location.pathname === "/") {
  window.location.href = "/predict";
}

document.getElementById("signupForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const name = document.getElementById("su-name").value.trim();
  const email = document.getElementById("su-email").value.trim().toLowerCase();
  const password = document.getElementById("su-password").value;

  const users = getUsers();
  if (users.some((u) => u.email === email)) {
    showError("An account with that email already exists.");
    return;
  }
  users.push({ name, email, password, joined: new Date().toISOString() });
  saveUsers(users);
  MA.setSession({ name, email });
  authError.style.display = "none";
  window.location.href = "/predict";
});

let pendingLoginUser = null;
let pendingLoginCode = null;

document.getElementById("loginForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const email = document.getElementById("li-email").value.trim().toLowerCase();
  const password = document.getElementById("li-password").value;

  const user = getUsers().find((u) => u.email === email && u.password === password);
  if (!user) {
    showError("No matching account. Check your email/password, or sign up.");
    return;
  }
  authError.style.display = "none";

  if (user.twoFAEnabled) {
    pendingLoginUser = user;
    pendingLoginCode = String(Math.floor(100000 + Math.random() * 900000));
    document.getElementById("loginDemoCode").textContent = pendingLoginCode;
    loginForm.classList.add("hidden");
    document.getElementById("twoFAStep").classList.remove("hidden");
    return;
  }
  MA.setSession({ name: user.name, email: user.email });
  window.location.href = "/predict";
});

document.getElementById("twoFALoginConfirmBtn").addEventListener("click", () => {
  const entered = document.getElementById("twoFALoginInput").value.trim();
  if (entered === pendingLoginCode) {
    MA.setSession({ name: pendingLoginUser.name, email: pendingLoginUser.email });
    window.location.href = "/predict";
  } else {
    showError("Incorrect verification code.");
  }
});
