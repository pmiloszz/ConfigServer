const state = {
  curApp: "",
  curEnv: "",
  byId: new Map(),
  filtered: [],
  sort: "key_asc",
  page: 1,
  pageSize: 20,
  readOnly: true,
  audit: [],
  rollouts: new Map(),
  selectedIds: new Set(),
  conflictMsg: "None",
  lastSync: null,
  autoRefreshSeconds: 60,
  autoRefreshTimer: null,
  density: "comfortable"
};
const SESSION_STATE_KEY = "configServerUiStateV1";
const SETTINGS_FLAG_KEYS = {
  compactDensity: "ui_setting_compact_density",
  autoRefreshEnabled: "ui_setting_auto_refresh_enabled"
};

const els = {
  keyInput: document.getElementById("in-apikey"),
  authPill: document.getElementById("auth-pill"),
  healthDot: document.getElementById("health-dot"),
  healthText: document.getElementById("health-text"),
  inApp: document.getElementById("in-app"),
  inEnv: document.getElementById("in-env"),
  dlApps: document.getElementById("dl-apps"),
  dlEnvs: document.getElementById("dl-envs"),
  btnLoad: document.getElementById("btn-load"),
  btnRefresh: document.getElementById("btn-refresh"),
  tabs: document.querySelectorAll(".tab"),
  sections: document.querySelectorAll(".section"),
  readonlyBanner: document.getElementById("readonly-banner"),
  ptitle: document.getElementById("ptitle"),
  pmeta: document.getElementById("pmeta"),
  tbody: document.getElementById("tbody"),
  inSearch: document.getElementById("in-search"),
  selSort: document.getElementById("sel-sort"),
  pageMeta: document.getElementById("page-meta"),
  selPageSize: document.getElementById("sel-page-size"),
  btnPrev: document.getElementById("btn-prev"),
  btnNext: document.getElementById("btn-next"),
  btnNew: document.getElementById("btn-new"),
  btnBulkOn: document.getElementById("btn-bulk-on"),
  btnBulkOff: document.getElementById("btn-bulk-off"),
  chkRolloutSelectAll: document.getElementById("chk-rollout-select-all"),
  smeta: document.getElementById("smeta"),
  rolloutBody: document.getElementById("rollout-body"),
  btnKillSwitch: document.getElementById("btn-killswitch"),
  auditList: document.getElementById("audit-list"),
  btnClearAudit: document.getElementById("btn-clear-audit"),
  stHealth: document.getElementById("st-health"),
  stAuth: document.getElementById("st-auth"),
  stSync: document.getElementById("st-sync"),
  stConflict: document.getElementById("st-conflict"),
  selTheme: document.getElementById("sel-theme"),
  setCompactDensity: document.getElementById("set-compact-density"),
  setAutoRefreshEnabled: document.getElementById("set-auto-refresh-enabled"),
  selAutoRefresh: document.getElementById("sel-auto-refresh"),
  selDensity: document.getElementById("sel-density"),
  toastBox: document.getElementById("toast-box")
};

function apiKey() { return els.keyInput.value.trim(); }
function x(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;"); }
function fmtDate(iso) {
  if (!iso) return "-";
  try { return new Date(iso).toLocaleString(); } catch { return String(iso); }
}
function toast(msg, type = "ok") {
  const el = document.createElement("div");
  el.className = `toast t-${type}`;
  el.textContent = msg;
  els.toastBox.appendChild(el);
  setTimeout(() => el.remove(), type === "err" ? 5000 : 3000);
}
function addAudit(action, detail) {
  state.audit.unshift({ ts: new Date().toISOString(), action, detail });
  state.audit = state.audit.slice(0, 60);
  renderAudit();
}
function applyTheme(theme) {
  const themeClasses = [
    "theme-light",
    "theme-midnight-cyan"
  ];
  document.body.classList.remove(...themeClasses);
  if (theme === "light") document.body.classList.add("theme-light");
  if (theme === "midnight-cyan") document.body.classList.add("theme-midnight-cyan");
  sessionStorage.setItem("uiTheme", theme);
}
function applyDensity(density) {
  state.density = density === "compact" ? "compact" : "comfortable";
  document.body.classList.toggle("density-compact", state.density === "compact");
  sessionStorage.setItem("uiDensity", state.density);
}
function applyAutoRefresh(seconds) {
  const value = Math.max(0, Number(seconds) || 0);
  state.autoRefreshSeconds = value;
  if (state.autoRefreshTimer) {
    clearInterval(state.autoRefreshTimer);
    state.autoRefreshTimer = null;
  }
  if (value > 0) {
    state.autoRefreshTimer = setInterval(() => {
      if (state.curApp && state.curEnv) loadFlags();
    }, value * 1000);
  }
  sessionStorage.setItem("uiAutoRefreshSeconds", String(value));
}
function persistUiState() {
  try {
    const snapshot = {
      curApp: state.curApp,
      curEnv: state.curEnv,
      sort: state.sort,
      page: state.page,
      pageSize: state.pageSize,
      readOnly: state.readOnly,
      conflictMsg: state.conflictMsg,
      lastSync: state.lastSync,
      selectedIds: Array.from(state.selectedIds),
      rollouts: Array.from(state.rollouts.entries()),
      audit: state.audit,
      activeTab: document.querySelector(".tab.active")?.dataset.tab || "flags",
      inApp: els.inApp?.value || "",
      inEnv: els.inEnv?.value || "",
      inSearch: els.inSearch?.value || "",
      apiKey: els.keyInput?.value || "",
      autoRefreshSeconds: state.autoRefreshSeconds,
      density: state.density
    };
    sessionStorage.setItem(SESSION_STATE_KEY, JSON.stringify(snapshot));
  } catch {}
}
function restoreUiState() {
  try {
    const raw = sessionStorage.getItem(SESSION_STATE_KEY);
    if (!raw) return;
    const s = JSON.parse(raw);
    state.curApp = s.curApp || "";
    state.curEnv = s.curEnv || "";
    state.sort = s.sort || "key_asc";
    state.page = Number(s.page || 1);
    state.pageSize = Number(s.pageSize || 20);
    state.conflictMsg = s.conflictMsg || "None";
    state.lastSync = s.lastSync || null;
    state.audit = Array.isArray(s.audit) ? s.audit : [];
    state.selectedIds = new Set(Array.isArray(s.selectedIds) ? s.selectedIds : []);
    state.rollouts = new Map(Array.isArray(s.rollouts) ? s.rollouts : []);
    const savedRefresh = s.autoRefreshSeconds ?? sessionStorage.getItem("uiAutoRefreshSeconds");
    state.autoRefreshSeconds = Number(savedRefresh ?? 60);
    state.density = s.density || sessionStorage.getItem("uiDensity") || "comfortable";
    if (els.inApp) els.inApp.value = s.inApp || state.curApp || "";
    if (els.inEnv) els.inEnv.value = s.inEnv || state.curEnv || "";
    if (els.inSearch) els.inSearch.value = s.inSearch || "";
    if (els.selSort) els.selSort.value = state.sort;
    if (els.selPageSize) els.selPageSize.value = String(state.pageSize);
    if (els.selAutoRefresh) els.selAutoRefresh.value = String(state.autoRefreshSeconds);
    if (els.selDensity) els.selDensity.value = state.density;
    if (els.keyInput && typeof s.apiKey === "string") els.keyInput.value = s.apiKey;
    if (state.lastSync && els.stSync) els.stSync.textContent = fmtDate(state.lastSync);
    if (els.stConflict) els.stConflict.textContent = state.conflictMsg;
    if (s.activeTab) switchTab(s.activeTab);
    applyDensity(state.density);
    applyAutoRefresh(state.autoRefreshSeconds);
  } catch {}
}

async function req(method, path, body, forceRead = false) {
  const isWrite = !["GET", "HEAD"].includes(method.toUpperCase());
  if (isWrite && state.readOnly && !forceRead) {
    throw { status: 403, detail: "Read-only mode: add API key to enable writes." };
  }
  const headers = { "Content-Type": "application/json" };
  const key = apiKey();
  if (key) headers["X-API-Key"] = key;
  const r = await fetch(path, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  if (r.status === 204) return null;
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw { status: r.status, detail: data.detail || r.statusText };
  return data;
}

function updateReadOnlyState() {
  state.readOnly = !apiKey();
  sessionStorage.setItem("apiKey", els.keyInput.value);
  els.readonlyBanner.classList.toggle("show", state.readOnly);
  els.authPill.textContent = state.readOnly ? "Auth mode: key required" : "Auth mode: authenticated";
  els.stAuth.innerHTML = state.readOnly ? '<span class="status-warn">Key required for reads and writes</span>' : '<span class="status-ok">Authenticated</span>';
  toggleWriteButtons();
  persistUiState();
}
function toggleWriteButtons() {
  const disable = state.readOnly;
  document.querySelectorAll("[data-write='1']").forEach((el) => {
    el.disabled = disable;
    el.title = disable ? "Add API key to enable write actions" : "";
  });
}

async function checkHealth() {
  try {
    const data = await fetch("/healthz").then((r) => r.json());
    const ok = data.status === "ok";
    els.healthDot.className = ok ? "ok" : "err";
    els.healthText.textContent = ok ? "healthy" : "degraded";
    els.stHealth.innerHTML = ok ? '<span class="status-ok">Healthy</span>' : '<span class="status-bad">Degraded</span>';
  } catch {
    els.healthDot.className = "err";
    els.healthText.textContent = "unreachable";
    els.stHealth.innerHTML = '<span class="status-bad">Unreachable</span>';
  }
}

function setLastSyncNow() {
  state.lastSync = new Date().toISOString();
  els.stSync.textContent = fmtDate(state.lastSync);
  persistUiState();
}

async function loadApps() {
  try {
    const apps = await req("GET", "/apps", undefined, true);
    els.dlApps.innerHTML = apps.map((v) => `<option value="${x(v)}">`).join("");
  } catch {}
}
async function loadEnvs(app) {
  if (!app) return;
  try {
    const envs = await req("GET", `/apps/${encodeURIComponent(app)}/envs`, undefined, true);
    els.dlEnvs.innerHTML = envs.map((v) => `<option value="${x(v)}">`).join("");
  } catch {}
}

function listFlags() { return Array.from(state.byId.values()); }
function isSettingFlagKey(key) {
  return Object.values(SETTINGS_FLAG_KEYS).includes(String(key || ""));
}
function getFlagByKey(key) {
  return listFlags().find((f) => f.key === key);
}
async function ensurePersistentSettingFlags() {
  if (!state.curApp || !state.curEnv || state.readOnly) return;
  const defs = [
    { key: SETTINGS_FLAG_KEYS.compactDensity, value: state.density === "compact", description: "Use compact table density for tighter UI spacing." },
    { key: SETTINGS_FLAG_KEYS.autoRefreshEnabled, value: state.autoRefreshSeconds > 0, description: "Enable automatic refresh polling for current app/env." }
  ];
  for (const d of defs) {
    if (getFlagByKey(d.key)) continue;
    try {
      const created = await req("POST", "/flags", {
        app: state.curApp,
        env: state.curEnv,
        key: d.key,
        value: d.value,
        description: d.description
      });
      state.byId.set(created.id, created);
      state.rollouts.set(created.id, { desired: created.value });
    } catch (e) {
      if (e.status !== 409) throw e;
    }
  }
}
function applySettingsFromFlags() {
  const compact = getFlagByKey(SETTINGS_FLAG_KEYS.compactDensity);
  if (compact) {
    const density = compact.value ? "compact" : "comfortable";
    applyDensity(density);
    if (els.selDensity) els.selDensity.value = density;
    if (els.setCompactDensity) els.setCompactDensity.checked = compact.value;
  }

  const refresh = getFlagByKey(SETTINGS_FLAG_KEYS.autoRefreshEnabled);
  if (refresh) {
    const refreshEnabled = !!refresh.value;
    if (els.setAutoRefreshEnabled) els.setAutoRefreshEnabled.checked = refreshEnabled;
    if (!refreshEnabled && state.autoRefreshSeconds > 0) {
      applyAutoRefresh(0);
    }
  }
}
function filteredFlags() {
  const q = els.inSearch.value.trim().toLowerCase();
  let flags = listFlags();
  if (q) {
    flags = flags.filter((f) =>
      String(f.key || "").toLowerCase().includes(q) ||
      String(f.description || "").toLowerCase().includes(q)
    );
  }
  const s = state.sort;
  flags.sort((a, b) => {
    const aSetting = isSettingFlagKey(a.key) ? 0 : 1;
    const bSetting = isSettingFlagKey(b.key) ? 0 : 1;
    if (aSetting !== bSetting) return aSetting - bSetting;
    if (s === "key_asc") return String(a.key).localeCompare(String(b.key));
    if (s === "key_desc") return String(b.key).localeCompare(String(a.key));
    if (s === "created_desc") return new Date(b.created_at || 0) - new Date(a.created_at || 0);
    if (s === "created_asc") return new Date(a.created_at || 0) - new Date(b.created_at || 0);
    if (s === "version_desc") return Number(b.version || 0) - Number(a.version || 0);
    return 0;
  });
  return flags;
}

function renderFlagsTable() {
  const flags = filteredFlags();
  state.filtered = flags;
  const total = flags.length;
  const pageCount = Math.max(1, Math.ceil(total / state.pageSize));
  if (state.page > pageCount) state.page = pageCount;
  const start = (state.page - 1) * state.pageSize;
  const pageRows = flags.slice(start, start + state.pageSize);
  const selectedCount = state.selectedIds.size;
  els.pmeta.textContent = `${listFlags().length} flag${listFlags().length !== 1 ? "s" : ""}${selectedCount ? `, ${selectedCount} selected` : ""}`;
  els.smeta.textContent = total === listFlags().length ? `${total} shown` : `${total} filtered`;
  els.pageMeta.textContent = `Page ${state.page}/${pageCount}`;
  els.btnPrev.disabled = state.page <= 1;
  els.btnNext.disabled = state.page >= pageCount;

  if (!state.curApp || !state.curEnv) {
    els.tbody.innerHTML = '<tr class="state-row"><td colspan="6">Enter app and environment, then load flags.</td></tr>';
    return;
  }
  if (!listFlags().length) {
    els.tbody.innerHTML = '<tr class="state-row"><td colspan="6">No flags yet. Create the first one.</td></tr>';
    return;
  }
  if (!pageRows.length) {
    els.tbody.innerHTML = '<tr class="state-row"><td colspan="6">No matches for current filter.</td></tr>';
    return;
  }
  els.tbody.innerHTML = pageRows.map(rowHtml).join("");
  state.selectedIds.forEach((id) => { if (!state.byId.has(id)) state.selectedIds.delete(id); });
  toggleWriteButtons();
  persistUiState();
}

function rowHtml(f) {
  const settingBadge = isSettingFlagKey(f.key)
    ? ' <span class="status-pill status-pill-setting">setting</span><span class="status-pill status-pill-setting">example</span>'
    : "";
  return `<tr id="r${f.id}">
    <td class="key-cell">${x(f.key)}${settingBadge}</td>
    <td>${f.value ? '<span class="status-ok status-strong">enabled</span>' : '<span class="status-bad status-strong">disabled</span>'}</td>
    <td class="desc-cell" id="dc${f.id}">${x(f.description || "-")}</td>
    <td class="date-cell">${fmtDate(f.created_at)}</td>
    <td class="ver-cell" id="v${f.id}">v${x(f.version)}</td>
    <td>
      <div class="act">
        <button class="btn btn-outline btn-sm" id="ebtn${f.id}" onclick="startEdit(${f.id})" data-write="1">Edit</button>
        <button class="btn btn-danger btn-sm" onclick="delFlag(${f.id}, '${x(f.key)}')" data-write="1">Delete</button>
      </div>
    </td>
  </tr>`;
}

function renderRollouts() {
  const flags = filteredFlags();
  if (!flags.length) {
    els.rolloutBody.innerHTML = '<tr class="state-row"><td colspan="6">Load flags to manage rollout controls.</td></tr>';
    if (els.chkRolloutSelectAll) els.chkRolloutSelectAll.checked = false;
    return;
  }
  els.rolloutBody.innerHTML = flags.map((f) => {
    const ro = state.rollouts.get(f.id) || { desired: f.value };
    const selected = state.selectedIds.has(f.id) ? "checked" : "";
    return `<tr>
      <td><input type="checkbox" class="row-select" ${selected} onchange="toggleRolloutSelect(${f.id}, this.checked)"></td>
      <td class="key-cell">${x(f.key)}${isSettingFlagKey(f.key) ? ' <span class="status-pill status-pill-setting">setting</span><span class="status-pill status-pill-setting">example</span>' : ""}</td>
      <td>${f.value ? '<span class="status-ok status-strong">enabled</span>' : '<span class="status-bad status-strong">disabled</span>'}</td>
      <td><label class="toggle"><input type="checkbox" ${ro.desired ? "checked" : ""} onchange="setDesiredState(${f.id}, this.checked)" ${state.readOnly ? "disabled" : ""}><span class="toggle-track"><span class="toggle-thumb"></span></span><span class="tlabel">${ro.desired ? "on" : "off"}</span></label></td>
      <td class="ver-cell">v${x(f.version)}</td>
      <td><button class="btn btn-outline btn-sm" onclick="applyRollout(${f.id})" data-write="1">Apply</button></td>
    </tr>`;
  }).join("");
  if (els.chkRolloutSelectAll) {
    const allChecked = flags.length && flags.every((f) => state.selectedIds.has(f.id));
    els.chkRolloutSelectAll.checked = allChecked;
  }
  toggleWriteButtons();
  persistUiState();
}
function toggleRolloutSelect(id, checked) {
  if (checked) state.selectedIds.add(id);
  else state.selectedIds.delete(id);
  renderFlagsTable();
  renderRollouts();
}
window.toggleRolloutSelect = toggleRolloutSelect;

function renderAudit() {
  if (!state.audit.length) {
    els.auditList.innerHTML = "<li>No activity yet.</li>";
    return;
  }
  els.auditList.innerHTML = state.audit.map((e) =>
    `<li><strong>${x(e.action)}</strong><br>${x(e.detail)}<br><span class="helper">${fmtDate(e.ts)}</span></li>`
  ).join("");
  persistUiState();
}

async function loadFlags() {
  const app = els.inApp.value.trim();
  const env = els.inEnv.value.trim();
  if (!app || !env) { toast("Enter both app and environment.", "warn"); return; }
  state.curApp = app;
  state.curEnv = env;
  els.ptitle.textContent = `${app} / ${env}`;
  els.tbody.innerHTML = '<tr class="state-row"><td colspan="6">Loading...</td></tr>';
  try {
    const flags = await req("GET", `/flags?app_name=${encodeURIComponent(app)}&env=${encodeURIComponent(env)}`, undefined, true);
    state.byId.clear();
    flags.forEach((f) => state.byId.set(f.id, f));
    flags.forEach((f) => {
      state.rollouts.set(f.id, { desired: f.value });
    });
    await ensurePersistentSettingFlags();
    applySettingsFromFlags();
    state.page = 1;
    state.selectedIds.clear();
    setLastSyncNow();
    state.conflictMsg = "None";
    els.stConflict.textContent = "None";
    renderFlagsTable();
    renderRollouts();
    addAudit("Flags loaded", `${flags.length} flags from ${app}/${env}`);
    await loadApps();
    await loadEnvs(app);
  } catch (e) {
    const msg = e.status === 401 ? "API key required (or invalid). Enter a valid key and try again." : `Load failed: ${x(e.detail || "network error")}`;
    els.tbody.innerHTML = `<tr class="state-row"><td colspan="6">${msg}</td></tr>`;
    toast(msg, "err");
  }
}

function startEdit(id) {
  const f = state.byId.get(id);
  if (!f) return;
  const dc = document.getElementById(`dc${id}`);
  const btn = document.getElementById(`ebtn${id}`);
  dc.innerHTML = `<input id="ei${id}" class="edit-input" maxlength="200" value="${x(f.description || "")}">`;
  btn.textContent = "Save";
  btn.onclick = () => saveEdit(id);
  const inp = document.getElementById(`ei${id}`);
  inp.focus();
  inp.select();
  inp.addEventListener("keydown", (e) => {
    if (e.key === "Enter") saveEdit(id);
    if (e.key === "Escape") cancelEdit(id);
  });
}
window.startEdit = startEdit;

async function saveEdit(id) {
  const f = state.byId.get(id);
  if (!f) return;
  const inp = document.getElementById(`ei${id}`);
  if (!inp) return;
  const desc = inp.value.trim() || null;
  const btn = document.getElementById(`ebtn${id}`);
  btn.disabled = true;
  try {
    const up = await req("PUT", `/flags/${id}`, { value: f.value, description: desc, version: f.version });
    state.byId.set(id, up);
    const dc = document.getElementById(`dc${id}`);
    dc.textContent = up.description || "-";
    document.getElementById(`v${id}`).textContent = `v${up.version}`;
    btn.disabled = false;
    btn.textContent = "Edit";
    btn.onclick = () => startEdit(id);
    addAudit("Description updated", `${f.key} description changed`);
    toast(`"${f.key}" updated`);
  } catch (e) {
    btn.disabled = false;
    if (e.status === 409) {
      state.conflictMsg = `Conflict on ${f.key}`;
      els.stConflict.textContent = state.conflictMsg;
      toast(`"${f.key}" changed elsewhere. Refreshing...`, "warn");
      setTimeout(loadFlags, 900);
    } else {
      toast(`Update failed: ${e.detail || "error"}`, "err");
      cancelEdit(id);
    }
  }
}

function cancelEdit(id) {
  const f = state.byId.get(id);
  if (!f) return;
  const dc = document.getElementById(`dc${id}`);
  dc.textContent = f.description || "-";
  const btn = document.getElementById(`ebtn${id}`);
  btn.textContent = "Edit";
  btn.disabled = false;
  btn.onclick = () => startEdit(id);
}

async function delFlag(id, key) {
  if (!confirm(`Delete flag "${key}"? This cannot be undone.`)) return;
  try {
    await req("DELETE", `/flags/${id}`);
    state.byId.delete(id);
    state.rollouts.delete(id);
    state.selectedIds.delete(id);
    renderFlagsTable();
    renderRollouts();
    addAudit("Flag deleted", `${key} removed`);
    toast(`"${key}" deleted`);
  } catch (e) {
    toast(`Delete failed: ${e.detail || "error"}`, "err");
  }
}
window.delFlag = delFlag;

function showCreate() {
  if (document.getElementById("create-row")) return;
  if (!state.curApp || !state.curEnv) {
    toast("Load flags first to set app and env context.", "warn");
    return;
  }
  const tr = document.createElement("tr");
  tr.id = "create-row";
  tr.innerHTML = `<td colspan="6">
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <input class="slim-input" id="nk" style="max-width:180px" placeholder="flag_key" maxlength="100">
      <input class="slim-input" id="nd" style="min-width:220px;flex:1" placeholder="Description (optional)" maxlength="200">
      <label class="toggle"><input id="nv" type="checkbox"><span class="toggle-track"><span class="toggle-thumb"></span></span><span class="tlabel" id="nvl">off</span></label>
      <button class="btn btn-primary btn-sm" id="btn-add" data-write="1">Add</button>
      <button class="btn btn-outline btn-sm" id="btn-cancel-create">Cancel</button>
    </div>
  </td>`;
  els.tbody.prepend(tr);
  document.getElementById("nv").addEventListener("change", (e) => {
    document.getElementById("nvl").textContent = e.target.checked ? "on" : "off";
  });
  document.getElementById("btn-cancel-create").addEventListener("click", () => tr.remove());
  document.getElementById("btn-add").addEventListener("click", submitCreate);
  toggleWriteButtons();
  document.getElementById("nk").focus();
}

async function submitCreate() {
  const key = document.getElementById("nk").value.trim();
  const desc = document.getElementById("nd").value.trim();
  const val = document.getElementById("nv").checked;
  if (!key) { toast("Key is required.", "warn"); return; }
  try {
    const created = await req("POST", "/flags", { app: state.curApp, env: state.curEnv, key, value: val, description: desc || null });
    state.byId.set(created.id, created);
    state.rollouts.set(created.id, { desired: created.value });
    const row = document.getElementById("create-row");
    if (row) row.remove();
    renderFlagsTable();
    renderRollouts();
    await loadApps();
    addAudit("Flag created", `${created.key} in ${state.curApp}/${state.curEnv}`);
    toast(`"${created.key}" created`);
  } catch (e) {
    if (e.status === 409) toast(`Flag "${key}" already exists.`, "warn");
    else toast(`Create failed: ${e.detail || "error"}`, "err");
  }
}

async function bulkSetOnCurrentPage(value) {
  const pageItems = getCurrentPageItems();
  if (!pageItems.length) return;
  if (!confirm(`Set ${pageItems.length} visible flags to ${value ? "on" : "off"}?`)) return;
  for (const f of pageItems) {
    try {
      const up = await req("PUT", `/flags/${f.id}`, { value, description: f.description, version: f.version });
      state.byId.set(up.id, up);
    } catch (e) {
      if (e.status === 409) {
        state.conflictMsg = "Conflict during bulk update";
        els.stConflict.textContent = state.conflictMsg;
      } else {
        toast(`Bulk update failed on ${f.key}`, "err");
      }
    }
  }
  renderFlagsTable();
  renderRollouts();
  addAudit("Bulk update", `Set ${pageItems.length} flags to ${value ? "on" : "off"}`);
  toast("Bulk update complete");
}

function getCurrentPageItems() {
  const all = filteredFlags();
  const start = (state.page - 1) * state.pageSize;
  return all.slice(start, start + state.pageSize);
}

function setDesiredState(id, desired) {
  const ro = state.rollouts.get(id) || { desired: false };
  ro.desired = !!desired;
  state.rollouts.set(id, ro);
  persistUiState();
}
window.setDesiredState = setDesiredState;

async function applyRollout(id) {
  const f = state.byId.get(id);
  if (!f) return;
  const ro = state.rollouts.get(id) || { desired: f.value };
  const nextValue = !!ro.desired;
  try {
    const up = await req("PUT", `/flags/${id}`, { value: nextValue, description: f.description, version: f.version });
    state.byId.set(id, up);
    state.rollouts.set(id, { desired: up.value });
    if (isSettingFlagKey(up.key)) applySettingsFromFlags();
    addAudit("Rollout applied", `${f.key}: set to ${up.value ? "on" : "off"}`);
    toast(`State updated for "${f.key}"`);
  } catch (e) {
    if (e.status === 409) {
      state.conflictMsg = `Conflict on rollout ${f.key}`;
      els.stConflict.textContent = state.conflictMsg;
      toast(`Conflict on "${f.key}", refreshing...`, "warn");
      setTimeout(loadFlags, 900);
    } else {
      toast(`Rollout update failed: ${e.detail || "error"}`, "err");
    }
  }
  renderFlagsTable();
  renderRollouts();
}
window.applyRollout = applyRollout;

async function killSwitch() {
  const selected = Array.from(state.selectedIds).map((id) => state.byId.get(id)).filter(Boolean);
  if (!selected.length) { toast("Select at least one flag in Rollouts tab first.", "warn"); return; }
  if (!confirm(`Disable ${selected.length} selected flags now?`)) return;
  for (const f of selected) {
    if (!f.value) continue;
    try {
      const up = await req("PUT", `/flags/${f.id}`, { value: false, description: f.description, version: f.version });
      state.byId.set(up.id, up);
    } catch (e) {
      if (e.status === 409) setTimeout(loadFlags, 900);
    }
  }
  renderFlagsTable();
  renderRollouts();
  addAudit("Emergency disable", `${selected.length} selected flags forced off`);
  toast("Emergency disable completed", "warn");
}

function switchTab(tabName) {
  els.tabs.forEach((t) => t.classList.toggle("active", t.dataset.tab === tabName));
  els.sections.forEach((s) => s.classList.toggle("active", s.id === `section-${tabName}`));
  persistUiState();
}

function wireEvents() {
  els.keyInput.value = sessionStorage.getItem("apiKey") || els.keyInput.value || "";
  els.keyInput.addEventListener("input", updateReadOnlyState);
  els.btnLoad.addEventListener("click", loadFlags);
  els.btnRefresh.addEventListener("click", loadFlags);
  els.inApp.addEventListener("change", (e) => loadEnvs(e.target.value.trim()));
  ["in-app", "in-env"].forEach((id) => document.getElementById(id).addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadFlags();
  }));

  const savedTheme = sessionStorage.getItem("uiTheme") || "dark";
  const allowedThemes = ["dark", "light", "midnight-cyan"];
  if (els.selTheme) {
    const initialTheme = allowedThemes.includes(savedTheme) ? savedTheme : "dark";
    els.selTheme.value = initialTheme;
    els.selTheme.addEventListener("change", () => applyTheme(els.selTheme.value));
    if (!allowedThemes.includes(savedTheme)) sessionStorage.setItem("uiTheme", "dark");
  }
  applyTheme(allowedThemes.includes(savedTheme) ? savedTheme : "dark");

  const savedDensity = sessionStorage.getItem("uiDensity") || state.density || "comfortable";
  if (els.selDensity) {
    els.selDensity.value = savedDensity === "compact" ? "compact" : "comfortable";
    els.selDensity.addEventListener("change", () => {
      applyDensity(els.selDensity.value);
      if (els.setCompactDensity) els.setCompactDensity.checked = state.density === "compact";
      persistUiState();
    });
  }
  applyDensity(savedDensity);

  const savedAutoRefresh = Number(sessionStorage.getItem("uiAutoRefreshSeconds") || state.autoRefreshSeconds || 60);
  if (els.selAutoRefresh) {
    els.selAutoRefresh.value = String(savedAutoRefresh);
    els.selAutoRefresh.addEventListener("change", () => {
      applyAutoRefresh(Number(els.selAutoRefresh.value));
      if (els.setAutoRefreshEnabled) els.setAutoRefreshEnabled.checked = Number(els.selAutoRefresh.value) > 0;
      persistUiState();
    });
  }
  applyAutoRefresh(savedAutoRefresh);

  if (els.setCompactDensity) {
    els.setCompactDensity.checked = state.density === "compact";
    els.setCompactDensity.addEventListener("change", async () => {
      const desiredCompact = !!els.setCompactDensity.checked;
      const density = desiredCompact ? "compact" : "comfortable";
      applyDensity(density);
      if (els.selDensity) els.selDensity.value = density;
      const f = getFlagByKey(SETTINGS_FLAG_KEYS.compactDensity);
      if (f && !state.readOnly) {
        try {
          const up = await req("PUT", `/flags/${f.id}`, { value: desiredCompact, description: f.description, version: f.version });
          state.byId.set(f.id, up);
          state.rollouts.set(f.id, { desired: up.value });
        } catch (e) {
          toast(`Compact density update failed: ${e.detail || "error"}`, "err");
        }
      }
      renderFlagsTable();
      renderRollouts();
      persistUiState();
    });
  }
  if (els.setAutoRefreshEnabled) {
    els.setAutoRefreshEnabled.checked = savedAutoRefresh > 0;
    els.setAutoRefreshEnabled.addEventListener("change", async () => {
      const enabled = !!els.setAutoRefreshEnabled.checked;
      if (!enabled) {
        applyAutoRefresh(0);
      } else if (Number(els.selAutoRefresh?.value || "0") <= 0) {
        applyAutoRefresh(60);
        if (els.selAutoRefresh) els.selAutoRefresh.value = "60";
      }
      const f = getFlagByKey(SETTINGS_FLAG_KEYS.autoRefreshEnabled);
      if (f && !state.readOnly) {
        try {
          const up = await req("PUT", `/flags/${f.id}`, { value: enabled, description: f.description, version: f.version });
          state.byId.set(f.id, up);
          state.rollouts.set(f.id, { desired: up.value });
        } catch (e) {
          toast(`Auto refresh update failed: ${e.detail || "error"}`, "err");
        }
      }
      renderFlagsTable();
      renderRollouts();
      persistUiState();
    });
  }

  els.tabs.forEach((tab) => tab.addEventListener("click", () => switchTab(tab.dataset.tab)));
  els.inSearch.addEventListener("input", () => { state.page = 1; renderFlagsTable(); persistUiState(); });
  els.selSort.addEventListener("change", () => { state.sort = els.selSort.value; renderFlagsTable(); persistUiState(); });
  els.selPageSize.addEventListener("change", () => {
    state.pageSize = Number(els.selPageSize.value);
    state.page = 1;
    renderFlagsTable();
    persistUiState();
  });
  els.btnPrev.addEventListener("click", () => { state.page = Math.max(1, state.page - 1); renderFlagsTable(); persistUiState(); });
  els.btnNext.addEventListener("click", () => { state.page = state.page + 1; renderFlagsTable(); persistUiState(); });

  els.btnNew.addEventListener("click", showCreate);
  els.btnBulkOn.addEventListener("click", () => bulkSetOnCurrentPage(true));
  els.btnBulkOff.addEventListener("click", () => bulkSetOnCurrentPage(false));
  els.btnKillSwitch.addEventListener("click", killSwitch);
  if (els.chkRolloutSelectAll) {
    els.chkRolloutSelectAll.addEventListener("change", (e) => {
      listFlags().forEach((f) => {
        if (e.target.checked) state.selectedIds.add(f.id);
        else state.selectedIds.delete(f.id);
      });
      renderFlagsTable();
      renderRollouts();
      persistUiState();
    });
  }
  els.btnClearAudit.addEventListener("click", () => { state.audit = []; renderAudit(); });
}

restoreUiState();
wireEvents();
updateReadOnlyState();
checkHealth();
setInterval(checkHealth, 30000);
loadApps();
renderFlagsTable();
renderRollouts();
renderAudit();
toggleWriteButtons();
