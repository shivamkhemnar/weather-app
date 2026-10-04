// RouteRisk India app v6: map-style From/To search + full route assessment + all buttons wired.
let chRisk = null, chTrend = null, running = true, allShips = [];
const CITIES = ["Mumbai","Nashik","Pune","Delhi","Jaipur","Chennai","Bangalore","Hyderabad","Kolkata","Ahmedabad"];

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) { const t = await r.text(); throw new Error(path + " -> " + r.status + " " + t.slice(0,120)); }
  return r.json();
}
const pill = l => `<span class="pill ${l}">${l}</span>`;
const money = n => "₹" + Math.round(n || 0).toLocaleString("en-IN");
const mapLink = c => `https://www.google.com/maps/search/${encodeURIComponent(c + ", India")}`;
const wxCity = () => (document.getElementById("wxCity") || {}).value || "Mumbai";
const tfCity = () => (document.getElementById("tfCity") || {}).value || "Mumbai";

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.classList.add("show");
  clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 2400);
}
function goTab(name) {
  document.querySelectorAll("#nav button").forEach(x => x.classList.toggle("active", x.dataset.tab === name));
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.id === "tab-" + name));
}
function hideAllSuggest() { ["fromSug","toSug"].forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = ""; }); }
document.addEventListener("click", e => { if (!e.target.closest(".rloc")) hideAllSuggest(); });

// --- navigation ---
document.getElementById("nav").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  goTab(b.dataset.tab);
});

// --- city matching (exact first, then substring) ---
function resolveCity(text) {
  const q = (text || "").trim().toLowerCase();
  if (!q) return null;
  const exact = CITIES.find(c => c.toLowerCase() === q);
  if (exact) return exact;
  return CITIES.find(c => c.toLowerCase().startsWith(q)) || CITIES.find(c => c.toLowerCase().includes(q)) || null;
}

// --- map-style From/To autocomplete ---
function suggestFor(inputId, sugId) {
  const q = (document.getElementById(inputId).value || "").trim().toLowerCase();
  const box = document.getElementById(sugId);
  if (!q) { box.innerHTML = ""; return; }
  const m = CITIES.filter(c => c.toLowerCase().includes(q)).slice(0, 6);
  box.innerHTML = m.length
    ? m.map(c => `<div class="sug" onclick="pickCity('${inputId}','${sugId}','${c}')">📍 <b>${c}</b></div>`).join("")
    : `<div class="sug none">Unknown city — try Mumbai, Pune, Delhi…</div>`;
}
function pickCity(inputId, sugId, name) {
  document.getElementById(inputId).value = name;
  document.getElementById(sugId).innerHTML = "";
}
function swapRoute() {
  const f = document.getElementById("fromIn"), t = document.getElementById("toIn");
  const tmp = f.value; f.value = t.value; t.value = tmp;
  toast("⇄ Swapped");
}
function planFromBar() {
  const a = resolveCity(document.getElementById("fromIn").value);
  const b = resolveCity(document.getElementById("toIn").value);
  if (!a || !b) { toast("Enter valid start + drop cities (e.g. Mumbai → Nashik)"); return; }
  if (a === b) { toast("Start and drop can't be the same city"); return; }
  document.getElementById("fromIn").value = a;
  document.getElementById("toIn").value = b;
  document.getElementById("routeFrom").value = a;
  document.getElementById("routeTo").value = b;
  showRoute(a, b, "balanced");
}

// --- full route assessment: risk + weather + traffic + cost/time + all options ---
async function planRoute(pref) {
  const a = document.getElementById("routeFrom").value, b = document.getElementById("routeTo").value;
  if (a === b) { toast("Pick two different cities"); return; }
  document.getElementById("fromIn").value = a;
  document.getElementById("toIn").value = b;
  await showRoute(a, b, pref || "balanced");
}
async function showRoute(a, b, pref) {
  const out = document.getElementById("routeOut");
  goTab("route");
  out.className = "";
  out.innerHTML = "⏳ Assessing <b>" + a + " → " + b + "</b> (" + pref + "): live weather, traffic, risk, costs…";
  try {
    const r = await api("/api/route/plan?origin=" + encodeURIComponent(a) + "&destination=" + encodeURIComponent(b) + "&preference=" + pref);
    const rows = (r.options || []).map((o, i) =>
      `<tr class="${o.action === r.picked.action ? "winner" : ""}">` +
      `<td>${i + 1}. ${o.action} ${o.action === r.picked.action ? "🏆" : ""}</td>` +
      `<td>${money(o.transport_cost)}</td><td>${money(o.penalty)}</td>` +
      `<td>${o.delay}d</td><td>${Math.round(o.risk)}</td><td>${Math.round(o.score).toLocaleString("en-IN")}</td></tr>`).join("");
    out.innerHTML =
      `<div class="route">` +
      `<div class="rhead"><b>🗺️ ${r.origin} → ${r.destination}</b> ${pill(r.risk_level)} <b>${r.risk_score}/100</b>` +
      `<a href="${r.map_url}" target="_blank"><button>🗺️ Open in Maps</button></a></div>` +
      `<div class="rgrid">` +
      `<div><b>📏 Distance</b><br>${r.distance_km} km road<br><span class="muted">~${r.eta_hours}h drive at current traffic speed</span></div>` +
      `<div><b>🌦️ ${a} weather</b><br>${r.origin_weather.condition || ""}, ${r.origin_weather.temperature}°C, rain ${r.origin_weather.rainfall_mm_last_hr !== undefined ? r.origin_weather.rainfall_mm_last_hr + " mm" : "—"}<br><span class="muted">src: ${r.origin_weather.source || ""}</span></div>` +
      `<div><b>🌦️ ${b} weather</b><br>${r.destination_weather.condition || ""}, ${r.destination_weather.temperature}°C, rain ${r.destination_weather.rainfall_mm_last_hr !== undefined ? r.destination_weather.rainfall_mm_last_hr + " mm" : "—"}<br><span class="muted">src: ${r.destination_weather.source || ""}</span></div>` +
      `<div><b>🚦 ${a} traffic</b><br>Congestion <b>${r.origin_traffic.congestion_level}%</b> — ${r.origin_traffic.route_status}<br><span class="muted">${r.origin_traffic.current_speed_kmh} km/h now (src: ${r.origin_traffic.source || ""})</span></div>` +
      `</div>` +
      `<div class="riskbox"><b>⚠️ Why this risk?</b><br>${(r.risk_factors || []).map(f => "• " + f).join("<br>")}</div>` +
      `<div class="pick">🏆 <b>${r.picked.action}</b> — ${money(r.picked.transport_cost)} + penalty ${money(r.picked.penalty)} • ${r.picked.delay} days • risk ${Math.round(r.picked.risk)}<br><span class="muted">${r.pick_reason} (mode: ${r.preference})</span></div>` +
      `<div class="row"><button onclick="showRoute('${a}','${b}','balanced')">⚖️ Balanced</button>` +
      `<button onclick="showRoute('${a}','${b}','cheapest')">💰 Cheapest (${money(r.cheapest.transport_cost)})</button>` +
      `<button onclick="showRoute('${a}','${b}','fastest')">⏱️ Fastest (${r.fastest.delay}d)</button></div>` +
      `<div class="tablewrap"><table class="optable"><thead><tr><th>Strategy</th><th>Transport</th><th>Penalty</th><th>Delay</th><th>Risk</th><th>Score</th></tr></thead><tbody>${rows}</tbody></table></div>` +
      `</div>`;
    toast("✓ " + a + " → " + b + ": " + r.picked.action);
  } catch (e) { out.innerHTML = "❌ Route assessment failed: " + e.message; }
}

// --- shipments filter (inside Shipments tab) ---
function filterShips(q) {
  q = (q || "").toLowerCase();
  document.querySelectorAll("#tblShip tbody tr").forEach(tr => {
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
  });
}

// --- clickable stat cards ---
function cardGo(tab, filter) {
  goTab(tab);
  if (tab === "risks" && filter) {
    document.querySelectorAll("#tblRisk tbody tr").forEach(tr => {
      tr.style.display = tr.textContent.includes(filter) ? "" : "none";
    });
    toast("⚠️ Showing " + filter + " risks (resets on next refresh)");
  } else if (tab === "shipments" && filter === "delayed") {
    document.querySelectorAll("#tblShip tbody tr").forEach(tr => {
      const t = tr.textContent.toLowerCase();
      tr.style.display = (t.includes("delayed") || t.includes("at risk")) ? "" : "none";
    });
    toast("🚚 Showing delayed shipments");
  }
}

// --- top controls ---
async function toggleRun() {
  running = !running;
  await api(running ? "/api/simulation/start" : "/api/simulation/stop", { method: "POST" });
  document.getElementById("runBtn").textContent = running ? "⏸ Pause" : "▶ Resume";
  toast(running ? "▶ Auto-refresh resumed (every 4h)" : "⏸ Auto-refresh paused");
  refresh();
}
async function refreshNow() { toast("⚡ Running full fleet check…"); await api("/api/simulation/tick", { method: "POST" }); toast("✓ Fleet check done"); refresh(); }
async function goCity(name) {
  const w = document.getElementById("wxCity"), t = document.getElementById("tfCity");
  if (w) w.value = name; if (t) t.value = name;
  goTab("weather"); loadWeather(); loadTraffic();
  toast("📍 " + name + " loaded");
}
async function checkShipment(id) { toast("⚡ Checking " + id + "…"); await api("/api/simulation/tick?shipment_id=" + id, { method: "POST" }); toast("✓ " + id + " checked"); refresh(); }
async function markRead(id) { await api("/api/alerts/" + id + "/read", { method: "POST" }); toast("✓ Alert cleared"); refresh(); }
async function markAllRead() {
  const s = await api("/api/dashboard/summary");
  for (const a of (s.recent_alerts || [])) { try { await api("/api/alerts/" + a.id + "/read", { method: "POST" }); } catch(e){} }
  toast("✓ All alerts cleared"); refresh();
}

// --- weather + traffic tabs ---
async function loadWeather() {
  const c = wxCity();
  document.getElementById("wxMap").href = mapLink(c);
  try {
    const w = await api("/api/weather/live?city=" + encodeURIComponent(c));
    document.getElementById("wxSrc").textContent = "• " + (w.source || "");
    document.getElementById("wxNow").innerHTML =
      `<b>${w.city || c}</b> — ${w.condition || ""} ${w.description || ""}<br>🌡️ ${w.temperature}°C &nbsp; 💧 ${w.humidity !== undefined ? w.humidity + "%" : "—"} &nbsp; 🌧️ ${w.rainfall_mm_last_hr !== undefined ? w.rainfall_mm_last_hr + " mm" : "—"} &nbsp; 💨 ${w.wind_speed || "—"} km/h`;
  } catch(e) { document.getElementById("wxNow").textContent = "Weather unavailable: " + e.message; }
  try {
    const f = await api("/api/weather/forecast?city=" + encodeURIComponent(c));
    document.querySelector("#tblFc tbody").innerHTML = (f.slots || []).map(s =>
      `<tr><td>${s.time}</td><td>${s.temp}</td><td>${s.condition}</td><td>${s.rain_mm}</td><td>${s.wind_kmh}</td></tr>`).join("");
    document.getElementById("fcMsg").textContent = "";
  } catch(e) { document.getElementById("fcMsg").textContent = "Forecast needs OPENWEATHER_API_KEY in .env (free at openweathermap.org)."; document.querySelector("#tblFc tbody").innerHTML = ""; }
}
async function loadTraffic() {
  const c = tfCity();
  document.getElementById("tfMap").href = mapLink(c);
  try {
    const t = await api("/api/traffic/live?city=" + encodeURIComponent(c));
    document.getElementById("tfSrc").textContent = "• " + (t.source || "");
    document.getElementById("tfNow").innerHTML =
      `<b>${t.city || c}</b> — congestion <b>${t.congestion_level}%</b> (${t.route_status || "—"})<br>🚗 current ${t.current_speed_kmh || "—"} km/h, free-flow ${t.free_flow_kmh || "—"} km/h`;
  } catch(e) { document.getElementById("tfNow").textContent = "Traffic unavailable: " + e.message; }
}
async function loadSettings() {
  try {
    const s = await api("/api/settings/status");
    document.getElementById("settings").innerHTML =
      `<div class="big">🌦️ Weather live: <b>${s.weather_live ? "✅ ON" : "❌ OFF (simulation)"}</b><br>🚦 Traffic live: <b>${s.traffic_live ? "✅ ON" : "❌ OFF (simulation)"}</b><br>🔄 Refresh every: <b>${s.refresh_hours} hours</b><br><span class="muted">${s.hint}</span></div>`;
    document.getElementById("refreshLbl").textContent = s.refresh_hours + " hours";
    document.getElementById("liveDot").className = "dot" + ((s.weather_live || s.traffic_live) ? " on" : "");
    document.getElementById("liveTxt").textContent = (s.weather_live || s.traffic_live) ? "LIVE DATA" : "SIMULATION MODE";
  } catch(e) {}
}

// --- main refresh ---
async function refresh() {
  try {
    const s = await api("/api/dashboard/summary");
    running = s.simulation_running;
    document.getElementById("runBtn").textContent = running ? "⏸ Pause" : "▶ Resume";
    const cards = [
      ["Shipments", s.total_shipments, "", "shipments", ""],
      ["Active", s.active_shipments, "ok", "shipments", ""],
      ["High risk", s.high_risk, "high", "risks", "HIGH"],
      ["Critical", s.critical, "crit", "risks", "CRITICAL"],
      ["Delayed", s.delayed_shipments, "high", "shipments", "delayed"],
      ["Impact ₹", Math.round(s.financial_impact).toLocaleString("en-IN"), "high", "decisions", ""],
      ["Alerts", s.active_alerts, "crit", "alerts", ""],
      ["Decisions", s.decisions, "ok", "decisions", ""]];
    document.getElementById("cards").innerHTML = cards.map(c =>
      `<div class="stat ${c[2]} clickable" onclick="cardGo('${c[3]}','${c[4]}')" title="Open ${c[0]}"><b>${c[1]}</b><span>${c[0]} →</span></div>`).join("");
    drawCharts(s);
    document.querySelector("#tblRisk tbody").innerHTML = (s.recent_risks || []).map(r =>
      `<tr><td>${r.shipment_id}</td><td>${r.score}</td><td>${pill(r.level)}</td><td>${r.at}</td></tr>`).join("");
    document.getElementById("decisions").innerHTML = (s.recent_decisions || []).map(d =>
      `<div class="dec"><b>${d.shipment_id} → ${d.action}</b> (${money(d.cost)}) ${pill(d.risk)}<br>${d.at}<br><a style="color:#38bdf8" href="/api/decisions/${d.id}" target="_blank">Full explanation + options →</a></div>`).join("") || "No decisions yet.";
    document.getElementById("alerts").innerHTML = (s.recent_alerts || []).map(a =>
      `<div class="alert"><b>${a.shipment_id}</b> ${pill(a.level)}<br>${a.message}<br><small>${a.at}</small><br><button onclick="markRead(${a.id})">✓ Mark read</button></div>`).join("") || "No alerts. System is calm.";
    const [ships, wx, tf, iot, inv, sup, ctr] = await Promise.all([
      api("/api/shipments"), api("/api/weather?limit=10"), api("/api/traffic?limit=10"),
      api("/api/iot?limit=10"), api("/api/inventory"), api("/api/suppliers"), api("/api/contracts")]);
    allShips = ships;
    document.querySelector("#tblShip tbody").innerHTML = ships.map(x =>
      `<tr><td>${x.shipment_id}</td><td>${x.product}</td><td>${x.origin}→${x.destination}</td><td>${x.current_status}</td><td>${Math.round(x.transportation_cost).toLocaleString("en-IN")}</td><td><button onclick="checkShipment('${x.shipment_id}')">⚡ Check</button></td></tr>`).join("");
    document.querySelector("#tblWx tbody").innerHTML = wx.map(x => `<tr><td>${x.shipment_id}</td><td>${x.weather_condition}</td><td>${x.rainfall}</td><td>${x.wind_speed}</td></tr>`).join("");
    document.querySelector("#tblTf tbody").innerHTML = tf.map(x => `<tr><td>${x.shipment_id}</td><td>${x.congestion_level}%</td><td>${x.average_speed}</td><td>${x.route_status}</td></tr>`).join("");
    document.querySelector("#tblIot tbody").innerHTML = iot.map(x => `<tr><td>${x.shipment_id}</td><td>${x.temperature}°C</td><td>${x.sensor_status}</td><td>${x.gps_position}</td></tr>`).join("");
    document.querySelector("#tblInv tbody").innerHTML = inv.map(x => `<tr><td>${x.product_name}</td><td>${x.current_stock}</td><td>${x.reorder_point}</td><td>${x.current_stock < x.safety_stock ? "🔴 Critical" : (x.current_stock < x.reorder_point ? "🟡 Low" : "🟢 OK")}</td></tr>`).join("");
    document.querySelector("#tblSup tbody").innerHTML = sup.map(x => `<tr><td>${x.supplier_name}</td><td>${x.reliability_score}</td><td>${x.current_delay_days}d</td></tr>`).join("");
    document.querySelector("#tblCtr tbody").innerHTML = ctr.map(x => `<tr><td>${x.contract_id}</td><td>${money(x.penalty_per_day)}</td><td>${x.maximum_delay_days}d</td></tr>`).join("");
  } catch (e) { console.error("refresh failed", e); }
}
function drawCharts(s) {
  if (!window.Chart) return;
  const d = s.risk_distribution || {};
  if (chRisk) chRisk.destroy();
  chRisk = new Chart(document.getElementById("chRisk"), { type: "doughnut",
    data: { labels: Object.keys(d), datasets: [{ data: Object.values(d), backgroundColor: ["#4ade80","#fbbf24","#fb923c","#f87171"] }] },
    options: { plugins: { legend: { labels: { color: "#e6edf7" } } } } });
  const t = (s.recent_risks || []).slice(0, 12).reverse();
  if (chTrend) chTrend.destroy();
  chTrend = new Chart(document.getElementById("chTrend"), { type: "line",
    data: { labels: t.map(x => x.shipment_id), datasets: [{ label: "Risk score", data: t.map(x => x.score), borderColor: "#38bdf8" }] },
    options: { scales: { x: { ticks: { color: "#93a1b8" } }, y: { min: 0, max: 100, ticks: { color: "#93a1b8" } } }, plugins: { legend: { labels: { color: "#e6edf7" } } } } });
}

// init (no missing-element crashes: every lookup is guarded)
(function init() {
  const opts = CITIES.map(c => `<option>${c}</option>`).join("");
  ["wxCity","tfCity","routeFrom","routeTo"].forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = opts; });
  const rt = document.getElementById("routeTo"); if (rt) rt.selectedIndex = 1;
  const w = document.getElementById("wxCity"); if (w) w.addEventListener("change", loadWeather);
  const t = document.getElementById("tfCity"); if (t) t.addEventListener("change", loadTraffic);
  const f = document.getElementById("fromIn"); if (f) { f.value = "Mumbai"; f.addEventListener("keydown", e => { if (e.key === "Enter") planFromBar(); }); }
  const d = document.getElementById("toIn"); if (d) { d.value = "Nashik"; d.addEventListener("keydown", e => { if (e.key === "Enter") planFromBar(); }); }
  loadSettings(); loadWeather(); loadTraffic(); refresh();
})();
setInterval(refresh, 10000);
setInterval(loadSettings, 60000);
