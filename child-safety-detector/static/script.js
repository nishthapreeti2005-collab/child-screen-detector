// ---------------------------------------------------------------
// Guardian Lens dashboard logic
// Talks to the Flask backend via simple fetch() calls.
// ---------------------------------------------------------------

const RING_CIRCUMFERENCE = 377; // 2 * PI * radius(60), matches style.css

let monitoringActive = false;
let currentFilter = "all";
let allScans = [];
let knownScanIds = new Set(); // used to detect *new* high-risk scans for toasts
let firstLoad = true;

const toggleMonitorBtn = document.getElementById("toggleMonitorBtn");
const scanNowBtn = document.getElementById("scanNowBtn");
const clearDataBtn = document.getElementById("clearDataBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const themeToggle = document.getElementById("themeToggle");
const filterTabs = document.getElementById("filterTabs");

// ---------- Theme (dark/light) ----------

function applyTheme(theme) {
  document.body.setAttribute("data-theme", theme);
  themeToggle.textContent = theme === "dark" ? "☀️" : "🌙";
  localStorage.setItem("guardianlens-theme", theme);
}

(function initTheme() {
  const saved = localStorage.getItem("guardianlens-theme");
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(saved || (prefersDark ? "dark" : "light"));
})();

themeToggle.addEventListener("click", () => {
  const current = document.body.getAttribute("data-theme");
  applyTheme(current === "dark" ? "light" : "dark");
});

// ---------- Helpers ----------

function badgeClass(riskLevel) {
  if (riskLevel === "High") return "badge-high";
  if (riskLevel === "Medium") return "badge-medium";
  return "badge-safe";
}

function riskColor(riskLevel) {
  if (riskLevel === "High") return "var(--high)";
  if (riskLevel === "Medium") return "var(--medium)";
  return "var(--safe)";
}

function ringColor(score) {
  if (score >= 80) return "var(--safe)";
  if (score >= 50) return "var(--medium)";
  return "var(--high)";
}

function animateCount(el, target) {
  const start = parseInt(el.textContent, 10) || 0;
  if (start === target) return;
  const duration = 500;
  const startTime = performance.now();
  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const value = Math.round(start + (target - start) * progress);
    el.textContent = value;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ---------- Category breakdown ----------

const CATEGORY_COLORS = {
  "Cyberbullying": "#E75454",
  "Profanity / Inappropriate Language": "#F0A93E",
  "Adult Content": "#D6467F",
  "Hate/Violent Language": "#9B2C2C",
  "Scam / Suspicious Link": "#D9B23C",
  "Suspicious Message": "#7C5CBF",
  "Safe": "#33B584",
};

const CATEGORY_ICONS = {
  "Cyberbullying": "🤬",
  "Profanity / Inappropriate Language": "🤐",
  "Adult Content": "🔞",
  "Hate/Violent Language": "⚔️",
  "Scam / Suspicious Link": "💰",
  "Suspicious Message": "🕵️",
  "Safe": "🟢",
};

function renderCategoryBreakdown(scans) {
  const el = document.getElementById("categoryBars");
  const nonSafe = scans.filter((s) => s.category !== "Safe");

  if (nonSafe.length === 0) {
    el.innerHTML = `<p class="empty-state">No risky content detected yet — nice and quiet 👍</p>`;
    return;
  }

  const counts = {};
  nonSafe.forEach((s) => { counts[s.category] = (counts[s.category] || 0) + 1; });
  const max = Math.max(...Object.values(counts));

  el.innerHTML = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([cat, count]) => `
      <div class="cat-row">
        <span class="cat-name">${cat}</span>
        <div class="cat-track"><div class="cat-fill" style="width:0%; background:${CATEGORY_COLORS[cat] || "var(--primary)"}" data-target="${(count / max) * 100}"></div></div>
        <span class="cat-count">${count}</span>
      </div>
    `)
    .join("");

  // animate bar widths in on next frame
  requestAnimationFrame(() => {
    el.querySelectorAll(".cat-fill").forEach((bar) => {
      bar.style.width = bar.dataset.target + "%";
    });
  });
}

// ---------- Toasts ----------

function showToast(message) {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

// ---------- Rendering ----------

function renderScans(data) {
  const { scans, stats } = data;
  allScans = scans;

  // Summary cards (animated count-up)
  animateCount(document.getElementById("statTotal"), stats.total);
  animateCount(document.getElementById("statSafe"), stats.safe);
  animateCount(document.getElementById("statMedium"), stats.medium);
  animateCount(document.getElementById("statHigh"), stats.high);

  // Safety score = 100 minus the average risk of recent scans
  let safetyScore = 100;
  if (scans.length > 0) {
    const avgRisk = scans.reduce((sum, s) => sum + s.risk_score, 0) / scans.length;
    safetyScore = Math.max(0, Math.round(100 - avgRisk));
  }
  document.getElementById("safetyScore").textContent = safetyScore;
  const ring = document.getElementById("ringProgress");
  const offset = RING_CIRCUMFERENCE * (1 - safetyScore / 100);
  ring.style.strokeDashoffset = offset;
  ring.style.stroke = ringColor(safetyScore);

  renderCategoryBreakdown(scans);

  // Toast for newly-seen High risk scans (skip on very first load)
  if (!firstLoad) {
    scans.forEach((s) => {
      if (!knownScanIds.has(s.id) && s.risk_level === "High") {
        showToast(`🚨 High risk detected: ${s.category}`);
      }
    });
  }
  knownScanIds = new Set(scans.map((s) => s.id));
  firstLoad = false;

  renderScanList();
}

function renderScanList() {
  const listEl = document.getElementById("scanList");
  const filtered = currentFilter === "all"
    ? allScans
    : allScans.filter((s) => s.risk_level === currentFilter);

  if (filtered.length === 0) {
    listEl.innerHTML = `<p class="empty-state">No scans in this category yet.</p>`;
    return;
  }

  listEl.innerHTML = filtered
    .map((s) => {
      const catColor = CATEGORY_COLORS[s.category] || "var(--primary)";
      const catIcon = CATEGORY_ICONS[s.category] || "🛡️";
      return `
      <div class="scan-item" data-id="${s.id}" style="border-left:3px solid ${catColor}">
        <span class="cat-icon-badge" style="background:${catColor}22; color:${catColor}">${catIcon}</span>
        <span class="badge ${badgeClass(s.risk_level)}">${s.risk_level} · ${s.risk_score}%</span>
        <div class="scan-body">
          <div class="scan-category" style="color:${catColor}">${s.category}</div>
          <div class="scan-reason">${s.reason || ""}</div>
          <div class="risk-bar-track"><div class="risk-bar-fill" style="width:${s.risk_score}%; background:${riskColor(s.risk_level)}"></div></div>
          ${
            s.risk_level !== "Safe"
              ? `<span class="scan-suggestion">💡 ${s.suggestion}</span>`
              : ""
          }
          <div class="scan-time">${s.timestamp} <span class="scan-expand-hint">· click for extracted text ▾</span></div>
          <div class="scan-detail">${s.extracted_text ? s.extracted_text : "(no readable text found on screen)"}</div>
        </div>
      </div>`;
    })
    .join("");

  listEl.querySelectorAll(".scan-item").forEach((item) => {
    item.addEventListener("click", () => item.classList.toggle("expanded"));
  });
}

// ---------- Filter tabs ----------

filterTabs.addEventListener("click", (e) => {
  const btn = e.target.closest(".tab");
  if (!btn) return;
  currentFilter = btn.dataset.filter;
  filterTabs.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  btn.classList.add("active");
  renderScanList();
});

// Clicking a stat card also filters the list
document.querySelectorAll(".stat-card").forEach((card) => {
  card.addEventListener("click", () => {
    const filter = card.dataset.filter;
    const matchingTab = filterTabs.querySelector(`.tab[data-filter="${filter}"]`);
    if (matchingTab) matchingTab.click();
  });
});

async function refreshScans() {
  const res = await fetch("/api/scans");
  const data = await res.json();
  renderScans(data);
}

// ---------- Monitoring controls ----------

function setMonitoringUI(active) {
  monitoringActive = active;
  const scanSweep = document.getElementById("scanSweep");
  if (active) {
    statusDot.className = "dot dot-on";
    statusText.textContent = "Monitoring Active";
    toggleMonitorBtn.textContent = "■ Stop Safety Monitoring";
    toggleMonitorBtn.classList.add("active");
    scanSweep.classList.add("active");
  } else {
    statusDot.className = "dot dot-off";
    statusText.textContent = "Monitoring Off";
    toggleMonitorBtn.textContent = "▶ Start Safety Monitoring";
    toggleMonitorBtn.classList.remove("active");
    scanSweep.classList.remove("active");
  }
}

toggleMonitorBtn.addEventListener("click", async () => {
  const endpoint = monitoringActive ? "/api/stop_monitoring" : "/api/start_monitoring";
  const res = await fetch(endpoint, { method: "POST" });
  const data = await res.json();
  setMonitoringUI(data.monitoring_active);
});

scanNowBtn.addEventListener("click", async () => {
  scanNowBtn.disabled = true;
  scanNowBtn.textContent = "Scanning...";
  try {
    const res = await fetch("/api/scan_once", { method: "POST" });
    const data = await res.json();
    if (!data.success) {
      alert("Scan failed: " + (data.error || "unknown error") + "\n\nRun 'python check_setup.py' to diagnose.");
    }
    await refreshScans();
  } catch (err) {
    alert("Could not reach the server. Is app.py still running?\n\n" + err);
  } finally {
    scanNowBtn.disabled = false;
    scanNowBtn.textContent = "🔍 Scan Now";
  }
});

clearDataBtn.addEventListener("click", async () => {
  if (!confirm("This will permanently delete all stored scan history. Continue?")) return;
  await fetch("/api/clear_data", { method: "POST" });
  knownScanIds = new Set();
  await refreshScans();
});

// ---------- Chatbot ----------

const chatToggle = document.getElementById("chatToggle");
const chatPanel = document.getElementById("chatPanel");
const chatClose = document.getElementById("chatClose");
const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const chatSend = document.getElementById("chatSend");
const chatSuggestions = document.getElementById("chatSuggestions");

chatToggle.addEventListener("click", () => chatPanel.classList.toggle("hidden"));
chatClose.addEventListener("click", () => chatPanel.classList.add("hidden"));

chatSuggestions.addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  const prompts = {
    "Bullying messages?": "What should I do if my child receives bullying messages?",
    "Stranger contact?": "What should I do if a stranger is contacting my child online?",
    "Screen time limits?": "How do I set healthy screen time limits for my child?",
  };
  chatInput.value = prompts[chip.textContent] || chip.textContent;
  sendChatMessage();
});

function addChatMessage(text, sender) {
  const row = document.createElement("div");
  row.className = `chat-row ${sender}`;

  const avatar = document.createElement("span");
  avatar.className = `chat-avatar ${sender === "bot" ? "bot-avatar" : "user-avatar"}`;
  avatar.textContent = sender === "bot" ? "🛡️" : "🙂";

  const bubble = document.createElement("div");
  bubble.className = `chat-msg ${sender}`;
  bubble.textContent = text;

  row.appendChild(avatar);
  row.appendChild(bubble);
  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return row;
}

function addTypingIndicator() {
  const row = document.createElement("div");
  row.className = "chat-row bot";

  const avatar = document.createElement("span");
  avatar.className = "chat-avatar bot-avatar";
  avatar.textContent = "🛡️";

  const bubble = document.createElement("div");
  bubble.className = "chat-msg bot typing";
  bubble.innerHTML = "<span></span><span></span><span></span>";

  row.appendChild(avatar);
  row.appendChild(bubble);
  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return row;
}

async function sendChatMessage() {
  const question = chatInput.value.trim();
  if (!question) return;
  addChatMessage(question, "user");
  chatInput.value = "";

  const typingEl = addTypingIndicator();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    typingEl.remove();
    addChatMessage(data.answer, "bot");
  } catch (err) {
    typingEl.remove();
    addChatMessage("Sorry, I couldn't reach the assistant. Is the server still running?", "bot");
  }
}

chatSend.addEventListener("click", sendChatMessage);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendChatMessage();
});

// ---------- Init ----------

async function init() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    setMonitoringUI(data.monitoring_active);
    await refreshScans();
  } catch (err) {
    document.getElementById("scanList").innerHTML =
      `<p class="empty-state">⚠ Could not connect to the backend server. Make sure "python app.py" is running, then refresh this page.</p>`;
  }
}

init();
setInterval(refreshScans, 5000); // live-refresh dashboard every 5s
