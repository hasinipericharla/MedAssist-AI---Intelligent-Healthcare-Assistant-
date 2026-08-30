// ---------------------------------------------------------------------
// Module 11: Medicine Reminder
// Stored via MA.getReminders/saveReminders (localStorage). Fires a
// browser Notification once per reminder per day while this tab stays
// open -- for real background push you'd need a service worker + a
// backend to schedule server-sent notifications.
// ---------------------------------------------------------------------

const form = document.getElementById("reminderForm");
const body = document.getElementById("reminderBody");
const emptyBlock = document.getElementById("reminderEmpty");

if ("Notification" in window && Notification.permission === "default") {
  Notification.requestPermission();
}

function render() {
  const list = MA.getReminders();
  if (list.length === 0) {
    body.innerHTML = "";
    emptyBlock.classList.remove("hidden");
    return;
  }
  emptyBlock.classList.add("hidden");
  body.innerHTML = list
    .map(
      (r, i) => `
      <tr>
        <td>${r.name}</td>
        <td>${r.time}</td>
        <td><button class="btn-secondary" data-index="${i}" style="padding:5px 12px;">Remove</button></td>
      </tr>`
    )
    .join("");

  body.querySelectorAll("button[data-index]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const list = MA.getReminders();
      list.splice(Number(btn.dataset.index), 1);
      MA.saveReminders(list);
      render();
    });
  });
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const name = document.getElementById("rm-name").value.trim();
  const time = document.getElementById("rm-time").value;
  if (!name || !time) return;
  const list = MA.getReminders();
  list.push({ name, time, lastFired: null });
  MA.saveReminders(list);
  form.reset();
  render();
});

// Check every 30s whether it's time to fire a reminder (only while the
// tab is open -- see note above about service workers for real push).
setInterval(() => {
  const now = new Date();
  const hhmm = now.toTimeString().slice(0, 5);
  const todayStr = now.toDateString();
  const list = MA.getReminders();
  let changed = false;

  list.forEach((r) => {
    if (r.time === hhmm && r.lastFired !== todayStr) {
      r.lastFired = todayStr;
      changed = true;
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification("Medicine reminder", { body: `Time to take ${r.name}` });
      } else {
        alert(`Time to take ${r.name}`);
      }
    }
  });

  if (changed) MA.saveReminders(list);
}, 30000);

render();
