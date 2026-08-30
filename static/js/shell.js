// ---------------------------------------------------------------------
// shell.js - runs on every page. Handles the sidebar toggle and exposes
// a tiny shared "store" object (window.MA) that every module page reads
// from. Everything here is localStorage-backed until the matching
// backend routes exist -- swap the MA.* functions for fetch() calls to
// your real API later without touching the pages that call them.
// ---------------------------------------------------------------------

window.MA = {
  KEYS: {
    profile: "ma_profile",
    history: "ma_history",
    reminders: "ma_reminders",
    session: "ma_session",
    feedback: "ma_feedback",
  },

  getProfile() {
    return JSON.parse(localStorage.getItem(this.KEYS.profile) || "null");
  },
  saveProfile(profile) {
    localStorage.setItem(this.KEYS.profile, JSON.stringify(profile));
  },

  getHistory() {
    return JSON.parse(localStorage.getItem(this.KEYS.history) || "[]");
  },
  addHistoryEntry(entry) {
    const list = this.getHistory();
    list.unshift({ ...entry, id: Date.now(), date: new Date().toISOString() });
    localStorage.setItem(this.KEYS.history, JSON.stringify(list.slice(0, 200)));
  },
  clearHistory() {
    localStorage.removeItem(this.KEYS.history);
  },

  getReminders() {
    return JSON.parse(localStorage.getItem(this.KEYS.reminders) || "[]");
  },
  saveReminders(list) {
    localStorage.setItem(this.KEYS.reminders, JSON.stringify(list));
  },

  getSession() {
    return JSON.parse(localStorage.getItem(this.KEYS.session) || "null");
  },
  setSession(session) {
    localStorage.setItem(this.KEYS.session, JSON.stringify(session));
  },
  clearSession() {
    localStorage.removeItem(this.KEYS.session);
  },

  computeBMI(heightCm, weightKg) {
    if (!heightCm || !weightKg) return null;
    const h = heightCm / 100;
    return +(weightKg / (h * h)).toFixed(1);
  },

  computeHealthScore({ bmi, symptomCount, topConfidence }) {
    let score = 100;
    if (bmi) {
      if (bmi < 18.5 || bmi >= 30) score -= 20;
      else if (bmi >= 25) score -= 10;
    }
    if (symptomCount) score -= Math.min(symptomCount * 4, 24);
    if (topConfidence) score -= Math.round((topConfidence / 100) * 20);
    score = Math.max(5, Math.min(100, score));
    let risk = "Low";
    if (score < 50) risk = "High";
    else if (score < 75) risk = "Medium";
    return { score, risk };
  },

  getUsers() {
    return JSON.parse(localStorage.getItem("ma_users") || "[]");
  },
  saveUsers(list) {
    localStorage.setItem("ma_users", JSON.stringify(list));
  },
  updateUser(email, changes) {
    const users = this.getUsers();
    const idx = users.findIndex((u) => u.email === email);
    if (idx === -1) return false;
    users[idx] = { ...users[idx], ...changes };
    this.saveUsers(users);
    return true;
  },

  getNotifications() {
    return JSON.parse(localStorage.getItem("ma_notifications") || "[]");
  },
  addNotification({ title, body }) {
    const list = this.getNotifications();
    list.unshift({ title, body, date: new Date().toISOString(), read: false });
    localStorage.setItem("ma_notifications", JSON.stringify(list.slice(0, 50)));
  },
  markAllNotificationsRead() {
    const list = this.getNotifications().map((n) => ({ ...n, read: true }));
    localStorage.setItem("ma_notifications", JSON.stringify(list));
  },
  clearNotifications() {
    localStorage.removeItem("ma_notifications");
  },
};

(function () {
  const publicPaths = ["/"];
  const session = JSON.parse(localStorage.getItem("ma_session") || "null");
  if (!session && !publicPaths.includes(window.location.pathname)) {
    window.location.href = "/";
  }

  const hamburger = document.getElementById("hamburgerBtn");
  const sidebar = document.getElementById("sidebar");
  if (hamburger && sidebar) {
    hamburger.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (window.innerWidth > 800) return;
      if (!sidebar.contains(e.target) && e.target !== hamburger) {
        sidebar.classList.remove("open");
      }
    });
  }

  function getSession() {
    try {
      return JSON.parse(localStorage.getItem("ma_session"));
    } catch {
      return null;
    }
  }

  const user = getSession();
  const topbarAvatar = document.getElementById("topbarAvatar");
  if (user && topbarAvatar) {
    topbarAvatar.textContent = user.name.charAt(0).toUpperCase();
  }

  const logoutBtn = document.getElementById("sidebarLogoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("ma_session");
      window.location.href = "/";
    });
  }

  const bellBtn = document.getElementById("notifBellBtn");
  const dropdown = document.getElementById("notifDropdown");
  const badge = document.getElementById("notifBadge");
  const list = document.getElementById("notifList");
  const clearBtn = document.getElementById("notifClearBtn");

  function renderNotifs() {
    const items = window.MA.getNotifications();
    const unread = items.filter((n) => !n.read).length;
    badge.textContent = unread;
    badge.classList.toggle("hidden", unread === 0);
    list.innerHTML = items.length
      ? items
          .map(
            (n) => `
        <div class="notif-item">
          <div class="notif-item-title">${n.title}</div>
          <div>${n.body}</div>
          <div class="notif-item-time">${new Date(n.date).toLocaleString()}</div>
        </div>`
          )
          .join("")
      : `<div class="notif-empty">No notifications yet.</div>`;
  }

  if (bellBtn) {
    bellBtn.addEventListener("click", () => {
      dropdown.classList.toggle("hidden");
      if (!dropdown.classList.contains("hidden")) {
        window.MA.markAllNotificationsRead();
        renderNotifs();
      }
    });
    clearBtn.addEventListener("click", () => {
      window.MA.clearNotifications();
      renderNotifs();
    });
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".notif-wrap")) dropdown.classList.add("hidden");
    });
    renderNotifs();
  }
})();