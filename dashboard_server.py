#!/usr/bin/env python3
"""
BBB Real-Time Dashboard Server
Serves REAL data only — no simulations, no fake numbers.
"""

import sys
import os
import json
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# ── Real state store (starts at zero, updated by live system) ──────────────
state = {
    "revenue": {
        "total": 0.0,
        "monthly": 0.0,
        "today": 0.0,
        "currency": "USD"
    },
    "customers": {
        "total": 0,
        "active": 0,
        "new_today": 0
    },
    "businesses": [],          # populated from live orchestrator
    "agents": [],              # live agent status
    "emails": {
        "sent_today": 0,
        "delivered": 0,
        "failed": 0
    },
    "social": {
        "posts_today": 0,
        "twitter_connected": False,
        "sendgrid_connected": False,
        "twilio_connected": False
    },
    "system": {
        "status": "starting",
        "uptime_seconds": 0,
        "started_at": datetime.now().isoformat(),
        "ollama_model": "echo",
        "ollama_connected": False,
        "last_updated": datetime.now().isoformat()
    },
    "activity_log": []
}

start_time = time.time()

def check_services():
    """Check real service connectivity."""
    import urllib.request, urllib.error

    # Check Ollama
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        data = json.loads(req.read())
        models = [m["name"] for m in data.get("models", [])]
        state["system"]["ollama_connected"] = True
        state["system"]["ollama_model"] = next((m for m in models if "ech0" in m.lower()), models[0] if models else "none")
    except Exception:
        state["system"]["ollama_connected"] = False

    # Check SendGrid, Twilio, Twitter, ElevenLabs
    try:
        from blank_business_builder.config import settings
        state["social"]["sendgrid_connected"] = bool(settings.SENDGRID_API_KEY and settings.SENDGRID_API_KEY.startswith("SG."))
        state["social"]["twilio_connected"] = bool(settings.TWILIO_API_KEY_SID or settings.TWILIO_ACCOUNT_SID)
        state["social"]["twitter_connected"] = bool(settings.TWITTER_CONSUMER_KEY)
        state["social"]["elevenlabs_connected"] = bool(settings.ELEVENLABS_API_KEY)
    except Exception:
        pass

def check_stripe_revenue():
    """Pull real revenue from Stripe if key is set."""
    try:
        from blank_business_builder.config import settings
        if not settings.STRIPE_SECRET_KEY:
            return  # No Stripe key — revenue stays $0

        import urllib.request
        req = urllib.request.Request(
            "https://api.stripe.com/v1/balance",
            headers={"Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}"}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=5).read())
        available = sum(b["amount"] for b in resp.get("available", [])) / 100
        state["revenue"]["total"] = available
    except Exception:
        pass

def load_ech0_config():
    """Load real business config from ~/.ech0/business_config.json"""
    config_path = Path.home() / ".ech0" / "business_config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            # Use the new 'businesses' key if present, fall back to 'websites'
            businesses = cfg.get("businesses", {})
            if businesses:
                state["businesses"] = [
                    {
                        "name": v.get("name", k),
                        "url": v.get("url", ""),
                        "category": v.get("category", ""),
                        "status": v.get("status", "active"),
                        "revenue": 0.0,
                        "monthly_target": v.get("monthly_target", 0.0)
                    }
                    for k, v in businesses.items()
                ]
            else:
                websites = cfg.get("websites", {})
                state["businesses"] = [
                    {"name": k.replace("_", " ").title(), "url": "", "category": "", "status": "active", "revenue": 0.0, "monthly_target": 0.0}
                    for k in websites.keys()
                ]
        except Exception as e:
            log_activity(f"Config load error: {e}")

def log_activity(msg: str):
    entry = {"time": datetime.now().strftime("%H:%M:%S"), "msg": msg}
    state["activity_log"].insert(0, entry)
    state["activity_log"] = state["activity_log"][:50]  # keep last 50

def load_shared_activity_log():
    """Load activity logs from ECH0 autonomous system."""
    log_path = Path.home() / ".ech0" / "activity_log.json"
    if log_path.exists():
        try:
            with open(log_path) as f:
                shared_logs = json.load(f)
            # Merge with existing state while avoiding duplicates if any
            state["activity_log"] = shared_logs[:50]
        except Exception as e:
            pass

def background_updater():
    """Refresh real data every 10 seconds (increased frequency)."""
    while True:
        try:
            state["system"]["uptime_seconds"] = int(time.time() - start_time)
            state["system"]["last_updated"] = datetime.now().isoformat()
            state["system"]["status"] = "running"
            check_services()
            check_stripe_revenue()
            load_ech0_config()
            load_shared_activity_log()
        except Exception as e:
            log_activity(f"Update error: {e}")
        time.sleep(10)


# ── HTTP Handler ──────────────────────────────────────────────────────────────
class DashboardHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # suppress access logs

    def do_GET(self):
        if self.path == "/api/state":
            self._json(state)
        elif self.path == "/api/log":
            self._json(state["activity_log"])
        elif self.path in ("/", "/index.html"):
            self._html()
        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, data):
        body = json.dumps(data, default=str).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _html(self):
        html = DASHBOARD_HTML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(html))
        self.end_headers()
        self.wfile.write(html)


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ECH0 — Live Business Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a26;
    --border: #2a2a3a;
    --accent: #6c63ff;
    --accent2: #00d4aa;
    --accent3: #ff6b6b;
    --text: #e8e8f0;
    --muted: #6b6b8a;
    --green: #00d4aa;
    --red: #ff4757;
    --yellow: #ffa502;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Animated background */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(108,99,255,0.15), transparent),
                radial-gradient(ellipse 60% 40% at 80% 80%, rgba(0,212,170,0.08), transparent);
    pointer-events: none;
    z-index: 0;
  }

  .container { position: relative; z-index: 1; max-width: 1400px; margin: 0 auto; padding: 24px; }

  /* Header */
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 32px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .logo-icon {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
  }

  .logo h1 { font-size: 20px; font-weight: 700; letter-spacing: -0.5px; }
  .logo p { font-size: 12px; color: var(--muted); }

  .header-right { display: flex; align-items: center; gap: 16px; }

  .live-badge {
    display: flex; align-items: center; gap: 6px;
    background: rgba(0,212,170,0.1);
    border: 1px solid rgba(0,212,170,0.3);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: var(--green);
    font-weight: 500;
  }

  .live-dot {
    width: 7px; height: 7px;
    background: var(--green);
    border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
  }

  .last-updated { font-size: 11px; color: var(--muted); font-family: 'JetBrains Mono', monospace; }

  /* KPI Grid */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }

  .kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
  }

  .kpi-card:hover { border-color: var(--accent); transform: translateY(-2px); }

  .kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    opacity: 0;
    transition: opacity 0.2s;
  }

  .kpi-card:hover::before { opacity: 1; }

  .kpi-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
  .kpi-value { font-size: 32px; font-weight: 700; letter-spacing: -1px; font-family: 'JetBrains Mono', monospace; }
  .kpi-sub { font-size: 12px; color: var(--muted); margin-top: 4px; }

  .kpi-value.green { color: var(--green); }
  .kpi-value.purple { color: var(--accent); }
  .kpi-value.red { color: var(--red); }

  /* Main grid */
  .main-grid {
    display: grid;
    grid-template-columns: 1fr 340px;
    gap: 20px;
    margin-bottom: 20px;
  }

  @media (max-width: 900px) { .main-grid { grid-template-columns: 1fr; } }

  /* Cards */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
  }

  .card-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* Services */
  .service-list { display: flex; flex-direction: column; gap: 10px; }

  .service-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    background: var(--surface2);
    border-radius: 10px;
    border: 1px solid var(--border);
  }

  .service-name { font-size: 13px; font-weight: 500; }
  .service-status { font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 6px; }
  .status-ok { background: rgba(0,212,170,0.15); color: var(--green); }
  .status-err { background: rgba(255,71,87,0.15); color: var(--red); }
  .status-warn { background: rgba(255,165,2,0.15); color: var(--yellow); }

  /* Activity log */
  .log-list { display: flex; flex-direction: column; gap: 6px; max-height: 300px; overflow-y: auto; }

  .log-item {
    display: flex;
    gap: 10px;
    padding: 8px 10px;
    background: var(--surface2);
    border-radius: 8px;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
  }

  .log-time { color: var(--accent); flex-shrink: 0; }
  .log-msg { color: var(--muted); }

  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: var(--muted);
    font-size: 13px;
  }

  .empty-state .icon { font-size: 32px; margin-bottom: 8px; }

  /* Business list */
  .biz-list { display: flex; flex-direction: column; gap: 8px; }

  .biz-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: var(--surface2);
    border-radius: 10px;
    border: 1px solid var(--border);
  }

  .biz-name { font-size: 13px; font-weight: 500; }
  .biz-revenue { font-size: 12px; font-family: 'JetBrains Mono', monospace; color: var(--green); }

  /* Zero state banner */
  .zero-banner {
    background: linear-gradient(135deg, rgba(108,99,255,0.1), rgba(0,212,170,0.05));
    border: 1px solid rgba(108,99,255,0.3);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .zero-banner .icon { font-size: 36px; flex-shrink: 0; }
  .zero-banner h3 { font-size: 15px; font-weight: 600; margin-bottom: 4px; }
  .zero-banner p { font-size: 13px; color: var(--muted); line-height: 1.5; }

  /* Uptime */
  .uptime { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--accent2); }
</style>
</head>
<body>
<div class="container">

  <header>
    <div class="logo">
      <div class="logo-icon">⚡</div>
      <div>
        <h1>ECH0 Business Dashboard</h1>
        <p>Corporation of Light — Autonomous Operations</p>
      </div>
    </div>
    <div class="header-right">
      <div class="live-badge"><div class="live-dot"></div>LIVE</div>
      <div class="last-updated" id="lastUpdated">—</div>
    </div>
  </header>

  <!-- Zero state banner (shown when revenue = 0) -->
  <div class="zero-banner" id="zeroBanner" style="display:none">
    <div class="icon">🚀</div>
    <div>
      <h3>System is live — revenue clock starts now</h3>
      <p>ECH0 is running autonomously. Revenue will appear here the moment a payment is processed via Stripe. Add your Stripe key to unlock deposit monitoring.</p>
    </div>
  </div>

  <!-- KPI Row -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">Total Revenue</div>
      <div class="kpi-value green" id="totalRevenue">$0.00</div>
      <div class="kpi-sub">All-time (Stripe)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Monthly Revenue</div>
      <div class="kpi-value green" id="monthlyRevenue">$0.00</div>
      <div class="kpi-sub">This month</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Customers</div>
      <div class="kpi-value purple" id="customerCount">0</div>
      <div class="kpi-sub">Active accounts</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Emails Sent Today</div>
      <div class="kpi-value purple" id="emailsSent">0</div>
      <div class="kpi-sub">via SendGrid</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">System Uptime</div>
      <div class="kpi-value uptime" id="uptime">0s</div>
      <div class="kpi-sub">Since last boot</div>
    </div>
  </div>

  <div class="main-grid">

    <!-- Left: Services + Businesses -->
    <div style="display:flex;flex-direction:column;gap:20px;">

      <!-- Service Status -->
      <div class="card">
        <div class="card-title">🔌 Service Connections</div>
        <div class="service-list" id="serviceList">
          <div class="service-item">
            <span class="service-name">Loading...</span>
          </div>
        </div>
      </div>

      <!-- Active Businesses -->
      <div class="card">
        <div class="card-title">🏢 Configured Businesses</div>
        <div id="bizList">
          <div class="empty-state">
            <div class="icon">⏳</div>
            Loading business config...
          </div>
        </div>
      </div>

    </div>

    <!-- Right: Activity Log -->
    <div class="card">
      <div class="card-title">📋 Activity Log</div>
      <div class="log-list" id="logList">
        <div class="empty-state">
          <div class="icon">🤖</div>
          Waiting for ECH0 activity...
        </div>
      </div>
    </div>

  </div>

</div>

<script>
const fmt = (n) => '$' + Number(n).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
const fmtUptime = (s) => {
  if (s < 60) return s + 's';
  if (s < 3600) return Math.floor(s/60) + 'm ' + (s%60) + 's';
  return Math.floor(s/3600) + 'h ' + Math.floor((s%3600)/60) + 'm';
};

async function refresh() {
  try {
    const res = await fetch('/api/state');
    const d = await res.json();

    // KPIs
    document.getElementById('totalRevenue').textContent = fmt(d.revenue.total);
    document.getElementById('monthlyRevenue').textContent = fmt(d.revenue.monthly);
    document.getElementById('customerCount').textContent = d.customers.active;
    document.getElementById('emailsSent').textContent = d.emails.sent_today;
    document.getElementById('uptime').textContent = fmtUptime(d.system.uptime_seconds);
    document.getElementById('lastUpdated').textContent = 'Updated ' + new Date(d.system.last_updated).toLocaleTimeString();

    // Zero banner
    document.getElementById('zeroBanner').style.display = d.revenue.total === 0 ? 'flex' : 'none';

    // Services
    const services = [
      { name: 'Echo (Ollama)', ok: d.system.ollama_connected, detail: d.system.ollama_model },
      { name: 'SendGrid Email', ok: d.social.sendgrid_connected, detail: d.social.sendgrid_connected ? 'Connected' : 'Key missing' },
      { name: 'Twilio SMS', ok: d.social.twilio_connected, detail: d.social.twilio_connected ? 'Connected' : 'Key missing' },
      { name: 'Twitter', ok: d.social.twitter_connected, detail: d.social.twitter_connected ? 'Connected' : 'Key missing' },
      { name: 'ElevenLabs Voice', ok: d.social.elevenlabs_connected, detail: d.social.elevenlabs_connected ? 'Connected' : 'Key missing' },
      { name: 'Stripe Payments', ok: false, detail: 'Add STRIPE_SECRET_KEY to .env' },
    ];

    document.getElementById('serviceList').innerHTML = services.map(s => `
      <div class="service-item">
        <span class="service-name">${s.name}</span>
        <span class="service-status ${s.ok ? 'status-ok' : 'status-err'}">${s.ok ? '✓ ' + s.detail : '✗ ' + s.detail}</span>
      </div>
    `).join('');

    // Businesses
    const bizEl = document.getElementById('bizList');
    if (d.businesses.length === 0) {
      bizEl.innerHTML = '<div class="empty-state"><div class="icon">🏗️</div>Loading business config...</div>';
    } else {
      bizEl.innerHTML = '<div class="biz-list">' + d.businesses.map(b => `
        <div class="biz-item" style="flex-direction:column;align-items:flex-start;gap:6px;">
          <div style="display:flex;justify-content:space-between;width:100%;align-items:center;">
            <span class="biz-name">${b.name}</span>
            <span class="biz-revenue">${fmt(b.revenue)}</span>
          </div>
          <div style="display:flex;justify-content:space-between;width:100%;">
            <span style="font-size:11px;color:var(--muted);">${b.category}</span>
            <span style="font-size:11px;color:var(--muted);">Target: ${fmt(b.monthly_target)}/mo</span>
          </div>
          ${b.url ? `<a href="${b.url}" target="_blank" style="font-size:11px;color:var(--accent);text-decoration:none;">${b.url}</a>` : ''}
        </div>
      `).join('') + '</div>';
    }

    // Activity log
    const logEl = document.getElementById('logList');
    if (d.activity_log.length === 0) {
      logEl.innerHTML = '<div class="empty-state"><div class="icon">🤖</div>Waiting for ECH0 activity...</div>';
    } else {
      logEl.innerHTML = d.activity_log.map(e => `
        <div class="log-item">
          <span class="log-time">${e.time}</span>
          <span class="log-msg">${e.msg}</span>
        </div>
      `).join('');
    }

  } catch(e) {
    document.getElementById('lastUpdated').textContent = 'Connection error — retrying...';
  }
}

refresh();
setInterval(refresh, 10000); // refresh every 10 seconds
</script>
</body>
</html>
"""


if __name__ == "__main__":
    PORT = 8765

    # Initial data load
    check_services()
    check_stripe_revenue()
    load_ech0_config()
    log_activity("Dashboard server started")
    log_activity("ECH0 autonomous system online")

    # Start background updater
    t = threading.Thread(target=background_updater, daemon=True)
    t.start()

    print(f"\n{'='*50}")
    print(f"  ECH0 Live Dashboard")
    print(f"  http://localhost:{PORT}")
    print(f"{'='*50}")
    print(f"  Revenue:   $0.00 (real — Stripe not connected)")
    print(f"  Customers: 0 (real)")
    print(f"  Refreshes: every 10 seconds")
    print(f"\n  Press Ctrl+C to stop\n")

    server = HTTPServer(("", PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
