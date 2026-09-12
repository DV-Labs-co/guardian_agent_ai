const riskPill = document.querySelector("#riskPill");
const houseMode = document.querySelector("#houseMode");
const progressText = document.querySelector("#progressText");
const meterBar = document.querySelector("#meterBar");
const householdEl = document.querySelector("#household");
const incidentsEl = document.querySelector("#incidents");
const decisionEl = document.querySelector("#decision");
const timelineEl = document.querySelector("#timeline");
const mcpLogEl = document.querySelector("#mcpLog");
const rulesEl = document.querySelector("#rules");
const toolsEl = document.querySelector("#tools");
const tvHeadline = document.querySelector("#tvHeadline");
const tvMessage = document.querySelector("#tvMessage");
const tvActions = document.querySelector("#tvActions");
const ruleForm = document.querySelector("#ruleForm");
const ruleInput = document.querySelector("#ruleInput");

const actions = {
  resetDemo: "reset",
  activateGuardian: "activate_guardian",
  expectedDelivery: "expected_delivery",
  unknownVisitor: "unknown_visitor",
  startWellness: "start_wellness_check",
  secondMiss: "mom_second_miss",
  unsafeUnlock: "unsafe_unlock_request",
  momResponds: "mom_responds",
  packageDelivery: "package_delivery",
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

async function simulate(action) {
  const data = await api("/api/simulate", {
    method: "POST",
    body: JSON.stringify({ action }),
  });
  render(data);
}

function titleCase(value) {
  return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function renderHousehold(household) {
  householdEl.innerHTML = "";
  for (const member of household.members) {
    const row = document.createElement("article");
    row.className = "context-row";
    row.innerHTML = `<div><strong></strong><small></small></div><span></span>`;
    row.querySelector("strong").textContent = member.name;
    row.querySelector("small").textContent = `${member.role} · ${member.routine}`;
    row.querySelector("span").textContent = member.status;
    householdEl.append(row);
  }
  for (const area of household.areas) {
    const row = document.createElement("article");
    row.className = "context-row";
    row.innerHTML = `<div><strong></strong><small></small></div><span></span>`;
    row.querySelector("strong").textContent = area.name;
    row.querySelector("small").textContent = "sensor area";
    row.querySelector("span").textContent = area.status;
    householdEl.append(row);
  }
}

function renderIncidents(incidents) {
  const active = incidents.filter((incident) => incident.status === "active");
  incidentsEl.innerHTML = "";
  if (!active.length) {
    incidentsEl.innerHTML = `<p class="muted">No active incidents.</p>`;
    return;
  }
  for (const incident of active) {
    const card = document.createElement("article");
    card.className = `incident risk-${incident.risk}`;
    card.innerHTML = `<strong></strong><small></small><span></span>`;
    card.querySelector("strong").textContent = incident.title;
    card.querySelector("small").textContent = titleCase(incident.kind);
    card.querySelector("span").textContent = titleCase(incident.risk);
    incidentsEl.append(card);
  }
}

function renderDecision(decisions) {
  const latest = decisions[decisions.length - 1];
  if (!latest) {
    decisionEl.className = "decision muted";
    decisionEl.textContent = "No decision yet.";
    return;
  }
  decisionEl.className = "decision";
  decisionEl.innerHTML = `
    <div class="decision-head">
      <div>
        <p class="eyebrow">Recommended Action</p>
        <strong>${titleCase(latest.recommendedAction)}</strong>
      </div>
      <span class="risk-${latest.risk}">${titleCase(latest.risk)}</span>
    </div>
    <p>${latest.reason}</p>
    <div class="pipeline">${latest.pipeline.map((step) => `<span>${step}</span>`).join("")}</div>
    <pre>${JSON.stringify({
      event: latest.event,
      context: latest.context,
      requiresApproval: latest.requiresApproval,
      blockedActions: latest.blockedActions,
    }, null, 2)}</pre>
  `;
}

function renderRules(rules) {
  rulesEl.innerHTML = "";
  for (const rule of rules.slice().reverse()) {
    const item = document.createElement("article");
    item.className = "rule";
    item.innerHTML = `<strong></strong><p></p><small></small>`;
    item.querySelector("strong").textContent = titleCase(rule.type);
    item.querySelector("p").textContent = rule.source;
    item.querySelector("small").textContent = `${rule.effect} · ${rule.severity}`;
    rulesEl.append(item);
  }
}

function renderTimeline(events) {
  timelineEl.innerHTML = "";
  for (const event of events.slice().reverse()) {
    const item = document.createElement("li");
    item.innerHTML = `<time></time><div><strong></strong><span></span></div>`;
    item.querySelector("time").textContent = new Date(event.at).toLocaleTimeString();
    item.querySelector("strong").textContent = `${event.event} · ${event.source}`;
    item.querySelector("span").textContent = event.detail;
    timelineEl.append(item);
  }
}

function renderMcpLog(calls) {
  mcpLogEl.innerHTML = "";
  if (!calls.length) {
    mcpLogEl.innerHTML = `<li class="muted">No MCP-style calls yet.</li>`;
    return;
  }
  for (const call of calls.slice().reverse()) {
    const item = document.createElement("li");
    item.innerHTML = `<time></time><div><strong></strong><span></span></div>`;
    item.querySelector("time").textContent = new Date(call.at).toLocaleTimeString();
    item.querySelector("strong").textContent = call.tool;
    item.querySelector("span").textContent = JSON.stringify(call.args);
    mcpLogEl.append(item);
  }
}

function renderFireTv(fireTv) {
  tvHeadline.textContent = fireTv.headline;
  tvMessage.textContent = fireTv.message;
  tvActions.innerHTML = "";
  for (const action of fireTv.actions) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = action;
    tvActions.append(button);
  }
}

function render(data) {
  riskPill.textContent = `${String(data.risk).toUpperCase()} RISK`;
  riskPill.className = `risk-pill risk-${data.risk}`;
  houseMode.textContent = titleCase(data.mode);
  progressText.textContent = `${data.progress}%`;
  meterBar.style.width = `${data.progress}%`;
  renderHousehold(data.household);
  renderIncidents(data.incidents);
  renderDecision(data.decisions);
  renderRules(data.rules);
  renderTimeline(data.events);
  renderMcpLog(data.mcp_calls);
  renderFireTv(data.fire_tv);
}

async function loadTools() {
  const data = await api("/api/mcp/tools");
  toolsEl.innerHTML = "";
  for (const tool of data.tools) {
    const item = document.createElement("article");
    item.className = "tool";
    item.innerHTML = `<strong></strong><small></small>`;
    item.querySelector("strong").textContent = tool.name;
    item.querySelector("small").textContent = tool.description;
    toolsEl.append(item);
  }
}

for (const [id, action] of Object.entries(actions)) {
  document.querySelector(`#${id}`).addEventListener("click", () => simulate(action));
}

ruleForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const rule = ruleInput.value.trim();
  if (!rule) return;
  const data = await api("/api/rules", {
    method: "POST",
    body: JSON.stringify({ rule }),
  });
  render(data);
});

api("/api/guardian").then(render);
loadTools();
