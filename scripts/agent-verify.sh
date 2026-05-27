#!/usr/bin/env bash
# Fast agent verification for sandbox PRs (Anthropic-style grep-friendly checks).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAST=false
if [[ "${1:-}" == "--fast" ]]; then
  FAST=true
fi

echo "[agent-verify] root=$ROOT fast=$FAST"

# Python syntax / import smoke
python -m compileall -q src/blank_business_builder 2>/dev/null || {
  echo "[agent-verify] compileall failed"
  exit 1
}

if command -v pytest >/dev/null 2>&1; then
  if $FAST; then
    pytest -q tests/test_middle_manager.py tests/test_enterprise_agent_policy.py \
      tests/test_company_pack.py tests/test_auto_judge_loop.py 2>/dev/null || {
      echo "[agent-verify] fast pytest subset failed (run full pytest locally)"
      exit 1
    }
  else
    pytest -q tests/ || exit 1
  fi
else
  echo "[agent-verify] pytest not installed; compileall only"
fi

echo "[agent-verify] OK"
