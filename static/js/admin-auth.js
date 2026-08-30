// ---------------------------------------------------------------------
// Separate admin auth, entirely independent of the user session (MA.*).
// Hardcoded demo credentials -- replace with a real admin login endpoint
// once you build one. This file does two jobs depending on the page:
//   - on admin-login.html: handles the login form submit
//   - on admin.html: gates the page, redirecting out if not logged in
// ---------------------------------------------------------------------

const ADMIN_CREDENTIALS = { email: "admin@medassist.ai", password: "admin123" };
const ADMIN_SESSION_KEY = "ma_admin_session";

function getAdminSession() {
  return JSON.parse(localStorage.getItem(ADMIN_SESSION_KEY) || "null");
}

const loginForm = document.getElementById("adminLoginForm");
if (loginForm) {
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = document.getElementById("ad-email").value.trim().toLowerCase();
    const password = document.getElementById("ad-password").value;
    const errorEl = document.getElementById("adminAuthError");

    if (email === ADMIN_CREDENTIALS.email && password === ADMIN_CREDENTIALS.password) {
      localStorage.setItem(ADMIN_SESSION_KEY, JSON.stringify({ email }));
      window.location.href = "/admin";
    } else {
      errorEl.textContent = "Invalid admin credentials.";
      errorEl.style.display = "block";
    }
  });
} else if (!getAdminSession()) {
  // We're on admin.html itself and there's no admin session -- gate it.
  window.location.href = "/admin-login";
}