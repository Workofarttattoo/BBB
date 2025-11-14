#!/usr/bin/env python3
"""
Get live stats from all running autonomous systems
"""
import json
import subprocess
import time
from pathlib import Path

def get_process_stats():
    """Get running process info"""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.split('\n')
        processes = []
        for line in lines:
            if 'autonomous_business_runner' in line and 'grep' not in line:
                parts = line.split()
                processes.append({
                    'pid': parts[1],
                    'cpu': parts[2] + '%',
                    'mem': parts[3] + '%',
                    'status': 'Running',
                    'command': ' '.join(parts[10:])
                })
        return processes
    except Exception as e:
        return [{'error': str(e)}]

def get_launchagent_status():
    """Get LaunchAgent status"""
    try:
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split('\n'):
            if 'com.bbb.autonomous' in line:
                parts = line.split()
                return {
                    'pid': parts[0],
                    'exit_code': parts[1],
                    'label': parts[2],
                    'status': 'Running' if parts[0] != '-' else 'Stopped'
                }
        return {'status': 'Not loaded'}
    except Exception as e:
        return {'error': str(e)}

def get_deployment_status():
    """Get Level-8-Agents deployment status"""
    plan_file = Path('/Users/noone/repos/BBB/level8_deployment_plan.json')
    if plan_file.exists():
        with open(plan_file) as f:
            data = json.load(f)
            return {
                'total_tasks': data['total_tasks'],
                'total_agents': data['total_agents'],
                'phase_1': data['status']['phase_1'],
                'phase_2': data['status']['phase_2'],
                'phase_3': data['status']['phase_3'],
                'deployment_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['deployment_timestamp']))
            }
    return {'status': 'No deployment plan found'}

def get_hive_status():
    """Get Hive Mind status from deployment plan"""
    plan_file = Path('/Users/noone/repos/BBB/level8_deployment_plan.json')
    if plan_file.exists():
        with open(plan_file) as f:
            data = json.load(f)
            return data.get('hive_status', {})
    return {}

# Print stats
print("=" * 80)
print("🚀 LIVE AUTONOMOUS BUSINESS STATS")
print("=" * 80)
print()

print("📊 RUNNING PROCESSES:")
processes = get_process_stats()
for p in processes:
    if 'error' in p:
        print(f"   Error: {p['error']}")
    else:
        print(f"   PID: {p['pid']} | CPU: {p['cpu']} | Memory: {p['mem']}")
        print(f"   Command: {p['command']}")
        print()

print("🔧 LAUNCHAGENT STATUS:")
la_status = get_launchagent_status()
for key, value in la_status.items():
    print(f"   {key}: {value}")
print()

print("⚡ LEVEL-8-AGENTS DEPLOYMENT:")
deploy_status = get_deployment_status()
for key, value in deploy_status.items():
    if isinstance(value, dict):
        print(f"   {key}:")
        for k, v in value.items():
            print(f"      {k}: {v}")
    else:
        print(f"   {key}: {value}")
print()

print("🧠 HIVE MIND STATUS:")
hive_status = get_hive_status()
if hive_status:
    print(f"   Total Agents: {hive_status.get('total_agents', 'N/A')}")
    print(f"   Active Agents: {hive_status.get('active_agents', 'N/A')}")
    print(f"   Messages Processed: {hive_status.get('messages_processed', 'N/A')}")
    print(f"   ECH0 Overseer: {'Active' if hive_status.get('ech0_overseer_active') else 'Inactive'}")
else:
    print("   No hive status data")
print()

print("=" * 80)
print(f"Stats generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
