/**
 * Natural-language command center — talk to CEO and agents in plain English.
 */

const EnterpriseChat = {
  context: {},
  open: true,

  init() {
    this.bindUi();
    this.renderSuggestions();
  },

  getBusinessName() {
    const tpl = document.getElementById("ent-business-template");
    if (tpl && tpl.value.trim()) return tpl.value.trim();
    const biz = State.businesses.find((b) => b.id === State.activeBusinessId);
    if (biz && biz.business_name) return biz.business_name;
    return "SaaS Micro-Tools Empire";
  },

  bindUi() {
    document.getElementById("btn-chat-toggle")?.addEventListener("click", () => {
      this.open = !this.open;
      const panel = document.getElementById("enterprise-chat-panel");
      const icon = document.getElementById("chat-toggle-icon");
      if (this.open) {
        panel.classList.remove("hidden");
        icon.className = "fa-solid fa-chevron-down";
      } else {
        panel.classList.add("hidden");
        icon.className = "fa-solid fa-chevron-up";
      }
    });

    document.getElementById("btn-chat-send")?.addEventListener("click", () =>
      this.sendMessage()
    );
    document.getElementById("enterprise-chat-input")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
  },

  renderSuggestions() {
    const wrap = document.getElementById("chat-suggestions");
    if (!wrap) return;
    const prompts = [
      "What needs my approval?",
      "Show automation policy",
      "Find 5 SaaS founders in the US",
      "CEO: review our sales pipeline",
      "Tell marketing to draft a launch email",
    ];
    wrap.innerHTML = "";
    prompts.forEach((text) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className =
        "text-xs px-2 py-1 rounded-full bg-blue-50 text-blue-800 border border-blue-100 hover:bg-blue-100 whitespace-nowrap";
      btn.textContent = text;
      btn.onclick = () => {
        document.getElementById("enterprise-chat-input").value = text;
        this.sendMessage();
      };
      wrap.appendChild(btn);
    });
  },

  appendMessage(text, role) {
    const box = document.getElementById("enterprise-chat-messages");
    if (!box) return;
    const div = document.createElement("div");
    div.className =
      role === "user"
        ? "chat-bubble chat-bubble-user ml-8"
        : "chat-bubble chat-bubble-assistant mr-8";
    div.textContent = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  },

  async sendMessage() {
    const input = document.getElementById("enterprise-chat-input");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    this.appendMessage(text, "user");

    const loading = document.createElement("div");
    loading.id = "chat-loading";
    loading.className = "chat-bubble chat-bubble-assistant mr-8 text-gray-400 italic";
    loading.textContent = "Thinking…";
    document.getElementById("enterprise-chat-messages").appendChild(loading);

    try {
      const res = await Auth.fetchWithAuth("/api/v1/enterprise/chat", {
        method: "POST",
        body: JSON.stringify({
          message: text,
          business_name: this.getBusinessName(),
          context: this.context,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Chat failed");

      if (data.context) this.context = data.context;
      loading.remove();
      this.appendMessage(data.reply, "assistant");

      if (data.actions && data.actions.length) {
        showToast(`Done: ${data.actions.join(", ")}`, "success");
      }
    } catch (err) {
      loading.remove();
      this.appendMessage(err.message || "Could not reach the command center.", "assistant");
      showToast(err.message, "error");
    }
  },
};
