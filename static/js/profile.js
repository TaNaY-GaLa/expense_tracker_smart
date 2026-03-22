/**
 * profile.js — Profile page, savings goals, dark mode switch
 */

// Sync dark mode switch with current state
document.addEventListener("DOMContentLoaded", () => {
  const sw = document.getElementById("darkModeSwitch");
  if (sw) sw.checked = document.body.classList.contains("dark-mode");
  loadGoals();
});

// ── Profile Update ─────────────────────────────────────────
async function saveProfile() {
  const email = document.getElementById("profileEmail")?.value.trim();
  const mobile = document.getElementById("profileMobile")?.value.trim();
  const language = document.getElementById("profileLanguage")?.value;

  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    showProfileAlert("Please enter a valid email address.", "danger"); return;
  }
  if (mobile && !/^\d{10}$/.test(mobile)) {
    showProfileAlert("Mobile must be a 10-digit number.", "danger"); return;
  }

  const res = await fetch("/api/profile/", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, mobile, language })
  });

  if (res.ok) {
    showProfileAlert("Profile updated successfully! ✅", "success");
  } else {
    const data = await res.json();
    showProfileAlert(data.error || "Update failed.", "danger");
  }
}

function showProfileAlert(msg, type) {
  const el = document.getElementById("profileAlert");
  if (!el) return;
  el.className = `alert alert-${type} py-2`;
  el.textContent = msg;
  el.classList.remove("d-none");
  setTimeout(() => el.classList.add("d-none"), 3500);
}

// ── Change Password ────────────────────────────────────────
async function changePassword() {
  const current = document.getElementById("currentPw")?.value;
  const newPw = document.getElementById("newPw")?.value;
  const confirm = document.getElementById("confirmPw")?.value;

  if (!current || !newPw || !confirm) {
    showPwAlert("Please fill all password fields.", "danger"); return;
  }
  if (newPw.length < 6) {
    showPwAlert("New password must be at least 6 characters.", "danger"); return;
  }
  if (newPw !== confirm) {
    showPwAlert("Passwords do not match.", "danger"); return;
  }

  const res = await fetch("/api/profile/", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: current, new_password: newPw })
  });

  if (res.ok) {
    showPwAlert("Password changed successfully! ✅", "success");
    ["currentPw","newPw","confirmPw"].forEach(id => { const el = document.getElementById(id); if(el) el.value=""; });
  } else {
    const data = await res.json();
    showPwAlert(data.error || "Failed to change password.", "danger");
  }
}

function showPwAlert(msg, type) {
  const el = document.getElementById("pwAlert");
  if (!el) return;
  el.className = `alert alert-${type} py-2`;
  el.textContent = msg;
  el.classList.remove("d-none");
  setTimeout(() => el.classList.add("d-none"), 3500);
}

// ── Savings Goals ──────────────────────────────────────────
let goals = [];

async function loadGoals() {
  const res = await fetch("/api/savings-goals/");
  const data = await res.json();
  goals = data.goals || [];
  renderGoals();
}

function renderGoals() {
  const el = document.getElementById("goalsList");
  if (!el) return;
  if (!goals.length) {
    el.innerHTML = `<p class="text-muted small text-center">No savings goals yet. Add one above!</p>`;
    return;
  }

  el.innerHTML = goals.map(g => {
    const pct = Math.min((g.saved / g.target) * 100, 100).toFixed(0);
    const remaining = Math.max(g.target - g.saved, 0);
    const deadline = new Date(g.deadline);
    const today = new Date();
    const daysLeft = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
    const daysLeftStr = daysLeft > 0 ? `${daysLeft} days left` : "Deadline passed";
    const dailyNeeded = daysLeft > 0 ? Math.ceil(remaining / daysLeft) : 0;

    return `
      <div class="goal-card">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <strong>${g.title}</strong>
            <div class="text-muted small">${daysLeftStr} · ₹${remaining.toLocaleString("en-IN")} remaining</div>
            ${dailyNeeded > 0 ? `<div class="small" style="color:var(--brown-main)">Spend max ₹${dailyNeeded.toLocaleString("en-IN")}/day to reach goal</div>` : ""}
          </div>
          <div class="text-end">
            <div class="small fw-bold" style="color:var(--brown-dark)">₹${g.saved.toLocaleString("en-IN")} / ₹${g.target.toLocaleString("en-IN")}</div>
            <div class="small text-muted">${pct}%</div>
          </div>
        </div>
        <div class="goal-progress mt-2">
          <div class="goal-progress-bar" style="width:${pct}%"></div>
        </div>
        <div class="d-flex gap-2 mt-2">
          <input type="number" class="form-control form-control-sm" id="updateSaved_${g.id}" placeholder="Update saved ₹" style="max-width:160px" value="${g.saved}">
          <button class="btn btn-sm btn-outline-brown" onclick="updateGoalSaved(${g.id})">Update</button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteGoal(${g.id})"><i class="bi bi-trash"></i></button>
        </div>
      </div>`;
  }).join("");
}

async function addGoal() {
  const title = document.getElementById("goalTitle")?.value.trim();
  const target = parseFloat(document.getElementById("goalTarget")?.value);
  const deadline = document.getElementById("goalDeadline")?.value;
  const saved = parseFloat(document.getElementById("goalSaved")?.value) || 0;

  if (!title || !target || !deadline) { alert("Please fill all goal fields."); return; }

  await fetch("/api/savings-goals/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, target, deadline, saved })
  });

  bootstrap.Modal.getOrCreateInstance(document.getElementById("goalModal")).hide();
  ["goalTitle","goalTarget","goalDeadline"].forEach(id => { const el=document.getElementById(id); if(el) el.value=""; });
  document.getElementById("goalSaved").value = "0";
  loadGoals();
}

async function updateGoalSaved(id) {
  const val = parseFloat(document.getElementById(`updateSaved_${id}`)?.value) || 0;
  await fetch(`/api/savings-goals/${id}/`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ saved: val })
  });
  loadGoals();
}

async function deleteGoal(id) {
  if (!confirm("Delete this goal?")) return;
  await fetch(`/api/savings-goals/${id}/`, { method: "DELETE" });
  loadGoals();
}
