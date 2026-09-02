// // ---------------------------------------------------------------------
// // Module 13: Authentication
// // Fake login/signup backed by localStorage under "ma_users" + a session
// // under MA.KEYS.session. This is NOT secure and is only meant to let
// // the rest of the app (nav "signed in" state, admin page) function
// // before your real JWT-based /api/auth/* routes exist. Passwords here
// // are stored in plain text in the browser -- never do this for real
// // auth; when you build the backend, delete fakeLogin/fakeSignup
// // entirely and call your API instead.
// // ---------------------------------------------------------------------

// const USERS_KEY = "ma_users";
// const authError = document.getElementById("authError");

// function getUsers() {
//   return JSON.parse(localStorage.getItem(USERS_KEY) || "[]");
// }
// function saveUsers(list) {
//   localStorage.setItem(USERS_KEY, JSON.stringify(list));
// }

// function showError(msg) {
//   authError.textContent = msg;
//   authError.style.display = "block";
// }

// // Tab switching between the Login and Sign up forms.
// const tabs = document.querySelectorAll(".auth-tab");
// const loginForm = document.getElementById("loginForm");
// const signupForm = document.getElementById("signupForm");
// if (tabs.length) {
//   tabs.forEach((tab) => {
//     tab.addEventListener("click", () => {
//       tabs.forEach((t) => t.classList.remove("active"));
//       tab.classList.add("active");
//       authError.style.display = "none";
//       if (tab.dataset.tab === "login") {
//         loginForm.classList.remove("hidden");
//         signupForm.classList.add("hidden");
//       } else {
//         signupForm.classList.remove("hidden");
//         loginForm.classList.add("hidden");
//       }
//     });
//   });
// }

// // If someone who's already logged in lands back on the login page,
// // send them straight into the app instead of showing the form again.
// if (MA.getSession() && window.location.pathname === "/") {
//   window.location.href = "/predict";
// }

// document.getElementById("signupForm").addEventListener("submit", (e) => {
//   e.preventDefault();
//   const name = document.getElementById("su-name").value.trim();
//   const email = document.getElementById("su-email").value.trim().toLowerCase();
//   const password = document.getElementById("su-password").value;

//   const users = getUsers();
//   if (users.some((u) => u.email === email)) {
//     showError("An account with that email already exists.");
//     return;
//   }
//   users.push({ name, email, password, joined: new Date().toISOString() });
//   saveUsers(users);
//   MA.setSession({ name, email });
//   authError.style.display = "none";
//   window.location.href = "/predict";
// });

// let pendingLoginUser = null;
// let pendingLoginCode = null;

// document.getElementById("loginForm").addEventListener("submit", (e) => {
//   e.preventDefault();
//   const email = document.getElementById("li-email").value.trim().toLowerCase();
//   const password = document.getElementById("li-password").value;

//   const user = getUsers().find((u) => u.email === email && u.password === password);
//   if (!user) {
//     showError("No matching account. Check your email/password, or sign up.");
//     return;
//   }
//   authError.style.display = "none";

//   if (user.twoFAEnabled) {
//     pendingLoginUser = user;
//     pendingLoginCode = String(Math.floor(100000 + Math.random() * 900000));
//     document.getElementById("loginDemoCode").textContent = pendingLoginCode;
//     loginForm.classList.add("hidden");
//     document.getElementById("twoFAStep").classList.remove("hidden");
//     return;
//   }
//   MA.setSession({ name: user.name, email: user.email });
//   window.location.href = "/predict";
// });

// document.getElementById("twoFALoginConfirmBtn").addEventListener("click", () => {
//   const entered = document.getElementById("twoFALoginInput").value.trim();
//   if (entered === pendingLoginCode) {
//     MA.setSession({ name: pendingLoginUser.name, email: pendingLoginUser.email });
//     window.location.href = "/predict";
//   } else {
//     showError("Incorrect verification code.");
//   }
// });

// ---------------------------------------------------------------------
// Module 13: Authentication
// Signup and login now call the real Flask backend (/api/signup,
// /api/verify-otp, /api/login) backed by MongoDB + email OTP.
// The post-login 2FA step below is still a client-only demo (no backend
// route for it yet) -- convert it the same way later if you want it real.
// ---------------------------------------------------------------------

const authError = document.getElementById("authError");

function showError(msg) {
  authError.textContent = msg;
  authError.style.display = "block";
}
function hideError() {
  authError.style.display = "none";
}

async function apiPost(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data;
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
      hideError();
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

// NOTE: signup's actual submission now happens via the button click
// handler in the inline script in auth.html (it calls /api/signup and
// shows the OTP step) -- this file no longer intercepts signupForm's
// submit event directly, to avoid double-handling.

let pendingLoginUser = null;
let pendingLoginCode = null;

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("li-email").value.trim().toLowerCase();
  const password = document.getElementById("li-password").value;

  hideError();
  try {
    const data = await apiPost("/api/login", { email, password });
    // Demo 2FA layer stays client-only for now -- no backend route yet.
    // If you want this real too, add a `twoFAEnabled` flag server-side
    // and check it here before setting the session.
    MA.setSession({ name: data.name, email });
    window.location.href = "/predict";
  } catch (err) {
    showError(err.message);
  }
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