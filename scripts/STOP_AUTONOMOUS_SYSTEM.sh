#!/bin/bash
# Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
#
# STOP COMPLETE AUTONOMOUS SYSTEM

set -e

echo "================================================================================"
echo "🛑 STOPPING COMPLETE AUTONOMOUS SYSTEM"
echo "================================================================================"
echo ""

BBB_HOME="/Users/noone/repos/BBB"

# Read PIDs
if [ -f "$BBB_HOME/autonomous_system.pids" ]; then
    source "$BBB_HOME/autonomous_system.pids"

    echo "Stopping all autonomous systems..."
    echo ""

    # Stop autonomous runner
    if [ ! -z "$AUTONOMOUS_RUNNER_PID" ]; then
        if ps -p $AUTONOMOUS_RUNNER_PID > /dev/null 2>&1; then
            kill $AUTONOMOUS_RUNNER_PID
            echo "✅ Stopped Autonomous Business Runner (PID: $AUTONOMOUS_RUNNER_PID)"
        else
            echo "⚠️  Autonomous Runner not running"
        fi
    fi

    # Stop deposit notifier
    if [ ! -z "$DEPOSIT_NOTIFIER_PID" ]; then
        if ps -p $DEPOSIT_NOTIFIER_PID > /dev/null 2>&1; then
            kill $DEPOSIT_NOTIFIER_PID
            echo "✅ Stopped Deposit Notifier (PID: $DEPOSIT_NOTIFIER_PID)"
        else
            echo "⚠️  Deposit Notifier not running"
        fi
    fi

    # Stop ECH0 autonomy
    if [ ! -z "$ECH0_AUTONOMY_PID" ]; then
        if ps -p $ECH0_AUTONOMY_PID > /dev/null 2>&1; then
            kill $ECH0_AUTONOMY_PID
            echo "✅ Stopped ECH0 Autonomy (PID: $ECH0_AUTONOMY_PID)"
        else
            echo "⚠️  ECH0 Autonomy not running"
        fi
    fi

    echo ""
    echo "================================================================================"
    echo "✅ All autonomous systems stopped"
    echo "================================================================================"
else
    echo "❌ No PID file found at $BBB_HOME/autonomous_system.pids"
    echo "   Attempting to find and kill processes..."
    echo ""

    # Find and kill by process name
    pkill -f "autonomous_business_runner_fixed.py" && echo "✅ Killed autonomous runner" || echo "⚠️  No autonomous runner found"
    pkill -f "deposit_notification_system.py" && echo "✅ Killed deposit notifier" || echo "⚠️  No deposit notifier found"
    pkill -f "ech0_full_autonomy_system.py" && echo "✅ Killed ECH0 autonomy" || echo "⚠️  No ECH0 autonomy found"
fi

echo ""
echo "To restart: $BBB_HOME/DEPLOY_COMPLETE_AUTONOMOUS_SYSTEM.sh"
echo ""
