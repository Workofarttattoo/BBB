/**
 * Enterprise Agent Ops — buttons for policy, approvals, Paperclip sync, leads.
 */

const EnterpriseOps = {
  STORAGE_KEYS: {
    businessTemplate: "bbb_enterprise_business_template",
    paperclipUrl: "bbb_paperclip_api_url",
    apolloCriteria: "bbb_apollo_criteria",
    apolloCount: "bbb_apollo_count",
  },

  init() {
    this.loadSavedSettings();
    this.bindButtons();
    this.syncBusinessTemplateFromSelector();
  },

  loadSavedSettings() {
    const tpl = localStorage.getItem(this.STORAGE_KEYS.businessTemplate);
    const pc = localStorage.getItem(this.STORAGE_KEYS.paperclipUrl);
    const crit = localStorage.getItem(this.STORAGE_KEYS.apolloCriteria);
    const count = localStorage.getItem(this.STORAGE_KEYS.apolloCount);

    const tplEl = document.getElementById("ent-business-template");
    const pcEl = document.getElementById("ent-paperclip-url");
    const critEl = document.getElementById("ent-apollo-criteria");
    const countEl = document.getElementById("ent-apollo-count");

    if (tplEl && tpl) tplEl.value = tpl;
    if (pcEl && pc) pcEl.value = pc;
    if (critEl && crit) critEl.value = crit;
    if (countEl && count) countEl.value = count;

    if (pcEl && !pcEl.value) pcEl.value = "http://127.0.0.1:3100";
    if (critEl && !critEl.value) critEl.value = "SaaS founders in US";
    if (countEl && !countEl.value) countEl.value = "5";
  },

  saveSettings() {
    const tplEl = document.getElementById("ent-business-template");
    const pcEl = document.getElementById("ent-paperclip-url");
    const critEl = document.getElementById("ent-apollo-criteria");
    const countEl = document.getElementById("ent-apollo-count");

    if (tplEl) localStorage.setItem(this.STORAGE_KEYS.businessTemplate, tplEl.value.trim());
    if (pcEl) localStorage.setItem(this.STORAGE_KEYS.paperclipUrl, pcEl.value.trim());
    if (critEl) localStorage.setItem(this.STORAGE_KEYS.apolloCriteria, critEl.value.trim());
    if (countEl) localStorage.setItem(this.STORAGE_KEYS.apolloCount, countEl.value);
  },

  syncBusinessTemplateFromSelector() {
    const tplEl = document.getElementById("ent-business-template");
    if (!tplEl || tplEl.value.trim()) return;

    const biz = State.businesses.find((b) => b.id === State.activeBusinessId);
    if (biz && biz.business_name) {
      tplEl.value = biz.business_name;
      this.saveSettings();
    }
  },

  getBusinessTemplate() {
    const tplEl = document.getElementById("ent-business-template");
    return (tplEl && tplEl.value.trim()) || "SaaS Micro-Tools Empire";
  },

  getPaperclipUrl() {
    const pcEl = document.getElementById("ent-paperclip-url");
    return (pcEl && pcEl.value.trim()) || "http://127.0.0.1:3100";
  },

  logOutput(label, data) {
    const pre = document.getElementById("ent-output");
    if (!pre) return;
    const stamp = new Date().toLocaleTimeString();
    const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
    pre.textContent = `[${stamp}] ${label}\n${text}\n\n${pre.textContent}`.slice(0, 12000);
  },

  async runAction(button, fn) {
    const original = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner inline-block mr-1"></span> Working…';
    this.saveSettings();
    try {
      await fn();
    } catch (err) {
      showToast(err.message || "Operation failed", "error");
      this.logOutput("ERROR", err.message || String(err));
    } finally {
      button.disabled = false;
      button.innerHTML = original;
    }
  },

  async apiGet(path) {
    const res = await Auth.fetchWithAuth(path);
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = body.detail || body.message || res.statusText;
      throw new Error(typeof detail === "object" ? JSON.stringify(detail) : detail);
    }
    return body;
  },

  async apiPost(path, payload) {
    const res = await Auth.fetchWithAuth(path, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = body.detail || body.message || res.statusText;
      throw new Error(typeof detail === "object" ? JSON.stringify(detail) : detail);
    }
    return body;
  },

  renderApprovals(pending) {
    const container = document.getElementById("ent-approvals-list");
    if (!container) return;

    if (!pending || pending.length === 0) {
      container.innerHTML =
        '<p class="text-sm text-gray-500 italic">No pending approvals.</p>';
      return;
    }

    container.innerHTML = "";
    pending.forEach((item) => {
      const card = document.createElement("div");
      card.className =
        "border border-gray-200 rounded-md p-3 bg-gray-50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2";

      const left = document.createElement("div");
      left.className = "text-sm";
      const title = document.createElement("div");
      title.innerHTML = `<strong>${item.action || item.gate_action || "action"}</strong><span class="text-gray-500"> · ${item.business_name || ""}</span>`;
      const idLine = document.createElement("div");
      idLine.className = "text-xs text-gray-600 mt-1 font-mono";
      idLine.textContent = item.id;
      left.appendChild(title);
      left.appendChild(idLine);

      const actions = document.createElement("div");
      actions.className = "flex gap-2 shrink-0";

      const approveBtn = document.createElement("button");
      approveBtn.type = "button";
      approveBtn.className =
        "px-3 py-1 text-xs rounded bg-green-600 text-white hover:bg-green-700";
      approveBtn.textContent = "Approve";
      approveBtn.onclick = () => this.resolveApproval(item.id, "approved");

      const rejectBtn = document.createElement("button");
      rejectBtn.type = "button";
      rejectBtn.className =
        "px-3 py-1 text-xs rounded bg-red-100 text-red-700 hover:bg-red-200";
      rejectBtn.textContent = "Reject";
      rejectBtn.onclick = () => this.resolveApproval(item.id, "rejected");

      actions.appendChild(approveBtn);
      actions.appendChild(rejectBtn);
      card.appendChild(left);
      card.appendChild(actions);
      container.appendChild(card);
    });
  },

  async resolveApproval(approvalId, status) {
    const data = await this.apiPost(`/api/v1/enterprise/approvals/${approvalId}/resolve`, {
      status,
    });
    showToast(`Approval ${status}`, "success");
    this.logOutput(`Approval ${status}`, data);
    await this.refreshApprovals(true);
  },

  async refreshApprovals(silent = false) {
    const biz = this.getBusinessTemplate();
    const data = await this.apiGet(
      `/api/v1/enterprise/approvals?business_name=${encodeURIComponent(biz)}`
    );
    this.renderApprovals(data.pending || []);
    if (!silent) {
      this.logOutput("Pending approvals", data);
      showToast(`${(data.pending || []).length} pending approval(s)`, "info");
    }
  },

  bindButtons() {
    const map = {
      "btn-ent-save-settings": (btn) =>
        this.runAction(btn, async () => {
          this.saveSettings();
          showToast("Sync settings saved", "success");
        }),
      "btn-ent-view-policy": (btn) =>
        this.runAction(btn, async () => {
          const biz = this.getBusinessTemplate();
          const data = await this.apiGet(`/api/v1/enterprise/policy/${encodeURIComponent(biz)}`);
          this.logOutput("Automation policy", data);
          showToast("Policy loaded", "success");
        }),
      "btn-ent-echo-health": (btn) =>
        this.runAction(btn, async () => {
          const data = await this.apiGet("/api/v1/echo-prime/health");
          this.logOutput("Echo Prime health", data);
          showToast("Echo Prime reachable", "success");
        }),
      "btn-ent-routing-labels": (btn) =>
        this.runAction(btn, async () => {
          const data = await this.apiGet("/api/v1/enterprise/routing/labels");
          this.logOutput("Paperclip routing labels", data);
          showToast("Routing labels loaded", "success");
        }),
      "btn-ent-mcp-bridge": (btn) =>
        this.runAction(btn, async () => {
          const data = await this.apiGet("/api/v1/enterprise/mcp-bridge");
          this.logOutput("MCP bridge manifest", data);
          showToast("MCP manifest loaded", "success");
        }),
      "btn-ent-refresh-approvals": (btn) =>
        this.runAction(btn, async () => {
          await this.refreshApprovals(false);
        }),
      "btn-ent-apollo-manual": (btn) =>
        this.runAction(btn, async () => {
          const criteria = document.getElementById("ent-apollo-criteria").value.trim();
          const count = parseInt(document.getElementById("ent-apollo-count").value, 10) || 5;
          const data = await this.apiPost("/api/v1/enterprise/leads/search", {
            criteria,
            count,
            mode: "manual",
            business_name: this.getBusinessTemplate(),
          });
          this.logOutput("Manual Apollo search", data);
          window._entLastLeads = data.leads || [];
          showToast(`Found ${data.count || 0} lead(s) (manual)`, "success");
        }),
      "btn-ent-apollo-agent": (btn) =>
        this.runAction(btn, async () => {
          const criteria = document.getElementById("ent-apollo-criteria").value.trim();
          const count = parseInt(document.getElementById("ent-apollo-count").value, 10) || 5;
          const data = await this.apiPost("/api/v1/enterprise/leads/search", {
            criteria,
            count,
            mode: "agent",
            business_name: this.getBusinessTemplate(),
          });
          this.logOutput("Agent Apollo search", data);
          window._entLastLeads = data.leads || [];
          showToast(`Found ${data.count || 0} lead(s) (agent)`, "success");
        }),
      "btn-ent-ingest-leads": (btn) =>
        this.runAction(btn, async () => {
          const leads = window._entLastLeads;
          if (!leads || !leads.length) {
            throw new Error("Run a lead search first — nothing to ingest.");
          }
          const data = await this.apiPost("/api/v1/enterprise/leads/ingest", {
            leads,
            business_name: this.getBusinessTemplate(),
            role: "sales",
          });
          this.logOutput("CRM ingest", data);
          showToast(`Ingested ${data.ingested || 0} lead(s)`, "success");
        }),
      "btn-ent-sync-paperclip": (btn) =>
        this.runAction(btn, async () => {
          const raw = document.getElementById("ent-paperclip-issues").value.trim();
          if (!raw) throw new Error("Paste Paperclip issues JSON in the box below first.");
          let issues;
          try {
            const parsed = JSON.parse(raw);
            issues = Array.isArray(parsed) ? parsed : parsed.issues || parsed.data || [];
          } catch {
            throw new Error("Invalid JSON — expected an array or { issues: [...] }");
          }
          const data = await this.apiPost("/api/v1/enterprise/paperclip/sync-issues", {
            business_name: this.getBusinessTemplate(),
            issues,
          });
          this.logOutput("Paperclip sync", data);
          showToast(`Synced ${issues.length} issue(s) into BBB queue`, "success");
        }),
      "btn-ent-open-paperclip": (btn) =>
        this.runAction(btn, async () => {
          window.open(this.getPaperclipUrl(), "_blank", "noopener,noreferrer");
          showToast("Opened Paperclip in new tab", "info");
        }),
      "btn-ent-clear-output": (btn) =>
        this.runAction(btn, async () => {
          const pre = document.getElementById("ent-output");
          if (pre) pre.textContent = "";
          showToast("Output cleared", "info");
        }),
    };

    Object.entries(map).forEach(([id, handler]) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener("click", () => handler(el));
    });

    document.getElementById("ent-business-template")?.addEventListener("change", () =>
      this.saveSettings()
    );
    document.getElementById("ent-paperclip-url")?.addEventListener("change", () =>
      this.saveSettings()
    );
  },

  onSettingsViewOpen() {
    this.syncBusinessTemplateFromSelector();
    this.refreshApprovals(true).catch(() => {});
  },
};
