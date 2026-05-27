#!/usr/bin/env bash
# =============================================================================
#  BBB AI Board of Directors — VPS Setup Script
#  Run this ONCE on your VPS to pull all models and configure Ollama.
#
#  Usage:
#    chmod +x scripts/setup_vps_board.sh
#    ./scripts/setup_vps_board.sh
#
#  Requirements:
#    - Ubuntu 22.04+ or Debian 12+
#    - 40GB+ disk space for all models
#    - Minimum 16GB RAM (24GB+ recommended)
#    - GPU optional but recommended (NVIDIA with CUDA or AMD with ROCm)
# =============================================================================

set -euo pipefail
BOLD="\033[1m"; GREEN="\033[92m"; YELLOW="\033[93m"; CYAN="\033[96m"; RESET="\033[0m"

log()  { echo -e "  ${GREEN}✓${RESET} $1"; }
info() { echo -e "  ${CYAN}ℹ${RESET}  $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $1"; }

echo -e "\n${BOLD}${CYAN}════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${CYAN}  BBB AI Board of Directors — VPS Setup${RESET}"
echo -e "${BOLD}${CYAN}════════════════════════════════════════════════${RESET}\n"

# ── 1. Install Ollama ────────────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
    info "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    log "Ollama installed"
else
    log "Ollama already installed: $(ollama --version)"
fi

# ── 2. Configure Ollama to listen on all interfaces ─────────────────────────
info "Configuring Ollama systemd service..."
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_KEEP_ALIVE=24h"
Environment="OLLAMA_MAX_LOADED_MODELS=3"
EOF
systemctl daemon-reload
systemctl enable ollama
systemctl restart ollama
sleep 3
log "Ollama service configured (listening on 0.0.0.0:11434)"

# ── 3. Pull board member models ──────────────────────────────────────────────
echo -e "\n${BOLD}Pulling AI board member models...${RESET}"
echo -e "(This may take a while depending on your connection)\n"

pull_model() {
    local name="$1"
    local tag="$2"
    info "Pulling $name ($tag)..."
    if ollama pull "$tag" 2>&1 | tail -1 | grep -q "success\|already\|up to date"; then
        log "$name ready"
    else
        ollama pull "$tag"
        log "$name pulled"
    fi
}

pull_model "COO — Hermes-3 (operations + function calling)" "hermes3:8b"
pull_model "CMO — Llama 3.2 (creative, marketing, fast)"   "llama3.2:3b"
pull_model "CFO — Qwen2.5 (financial analysis)"            "qwen2.5:7b"
pull_model "CEO — DeepSeek-R1 (reasoning, big decisions)"  "deepseek-r1:14b"
pull_model "CSO — Qwen3 MoE (strategy, bold moves)"        "qwen3:30b-a3b"
pull_model "Vision — Qwen2.5-VL (screen understanding)"    "qwen2.5-vl:3b"

# CTO model is large (16B) — ask first
echo ""
read -rp "  Pull CTO model (deepseek-coder-v2:16b, ~10GB)? [y/N] " pull_cto
if [[ "${pull_cto,,}" == "y" ]]; then
    pull_model "CTO — DeepSeek-Coder-V2 (technical, architecture)" "deepseek-coder-v2:16b"
else
    warn "Skipped CTO model — pull later with: ollama pull deepseek-coder-v2:16b"
fi

# Grok — needs massive VRAM, skip unless confirmed
echo ""
read -rp "  Pull Grok-1 CSO model (314B MoE, needs 80GB+ VRAM)? [y/N] " pull_grok
if [[ "${pull_grok,,}" == "y" ]]; then
    pull_model "CSO — Grok-1 (strategy)" "joefamous/grok-1:314b-q2_K"
else
    warn "Skipped Grok-1 — using Qwen3:30b-a3b as CSO fallback (already pulled)"
fi

# ── 4. Install Python browser automation deps ────────────────────────────────
echo -e "\n${BOLD}Installing Echo Operator dependencies...${RESET}"
pip install -q playwright pyautogui pillow 2>/dev/null || \
    pip3 install -q playwright pyautogui pillow
python -m playwright install chromium --with-deps 2>/dev/null || \
    python3 -m playwright install chromium --with-deps
apt-get install -y -q xdotool 2>/dev/null || warn "xdotool install skipped (may need sudo)"
log "Echo Operator deps installed"

# ── 5. Verify everything ─────────────────────────────────────────────────────
echo -e "\n${BOLD}${CYAN}Board Status:${RESET}"
ollama list | while IFS= read -r line; do echo "  $line"; done

VPS_IP=$(curl -s https://ipv4.icanhazip.com 2>/dev/null || hostname -I | awk '{print $1}')
echo -e "\n${BOLD}${GREEN}Setup complete!${RESET}"
echo -e "\nAdd to your BBB .env:"
echo -e "  ${CYAN}HERMES_VPS_URL=http://${VPS_IP}:11434${RESET}"
echo -e "  ${CYAN}CEO_VPS_URL=http://${VPS_IP}:11434${RESET}"
echo -e "  ${CYAN}COO_VPS_URL=http://${VPS_IP}:11434${RESET}"
echo -e "  ${CYAN}CFO_VPS_URL=http://${VPS_IP}:11434${RESET}"
echo -e "  ${CYAN}CTO_VPS_URL=http://${VPS_IP}:11434${RESET}"
echo -e "  ${CYAN}CMO_VPS_URL=http://${VPS_IP}:11434${RESET}"
echo -e "  ${CYAN}CSO_VPS_URL=http://${VPS_IP}:11434${RESET}"
echo -e "  ${CYAN}VISION_MODEL=qwen2.5-vl:3b${RESET}\n"
