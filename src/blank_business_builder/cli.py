"""
Command-line entrypoint for the Blank Business Builder.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import argparse
import json
import webbrowser
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .onboarding import OnboardingAssistant


def serialize(obj: Any) -> Any:
    if hasattr(obj, "__dict__"):
        return {
            key: serialize(value)
            for key, value in obj.__dict__.items()
            if not key.startswith("_")
        }
    if isinstance(obj, (list, tuple)):
        return [serialize(item) for item in obj]
    return obj


def launch_gui() -> None:
    """Launch the Business Builder GUI in default browser."""
    gui_path = Path(__file__).parent / "business_builder_gui.html"

    if not gui_path.exists():
        print(f"[error] GUI file not found at {gui_path}")
        return

    webbrowser.open(f"file://{gui_path}")
    print(f"[info] Business Builder GUI launched: {gui_path}")
    print("[info] The GUI is running in your browser.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Better Business Builder - Autonomous Passive Income Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch interactive GUI
  bbb --gui

  # Deploy autonomous business (Level 6 agents)
  bbb --autonomous --business "AI Chatbot Integration Service" --duration 24

  # Run CLI onboarding interview
  bbb

  # Export recommendations as JSON
  bbb --json > recommendations.json

Features:
  - Level 6 autonomous agents run business hands-free
  - 32+ curated business ideas across 11 industries
  - Quantum-inspired optimization ranking
  - Autonomous marketing, sales, fulfillment, support
  - Financial projections and business plan generation
  - Beautiful web GUI with real-time monitoring
        """
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the web-based GUI in your browser"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--autonomous",
        action="store_true",
        help="Deploy Level 6 autonomous agents to run business hands-free"
    )
    parser.add_argument(
        "--business",
        type=str,
        help="Business concept to run autonomously (required with --autonomous)"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=24.0,
        help="Hours to run autonomous business (default: 24)"
    )
    parser.add_argument(
        "--founder",
        type=str,
        default="Founder",
        help="Your name (for personalization)"
    )

    args = parser.parse_args()

    if args.gui:
        launch_gui()
        return

    if args.autonomous:
        if not args.business:
            print("[error] --business is required when using --autonomous")
            print("Example: bbb --autonomous --business 'AI Chatbot Integration Service'")
            return

        # Launch autonomous business
        import asyncio
        from .autonomous_business import launch_autonomous_business

        print(f"[info] Deploying Level 6 autonomous agents for: {args.business}")
        print(f"[info] Duration: {args.duration} hours")
        print(f"[info] Founder: {args.founder}")
        print("\n🚀 Launching autonomous business operation...\n")

        metrics = asyncio.run(launch_autonomous_business(
            business_concept=args.business,
            founder_name=args.founder,
            duration_hours=args.duration
        ))

        print("\n" + "="*60)
        print("✅ AUTONOMOUS OPERATION COMPLETE")
        print("="*60)
        print(json.dumps(metrics, indent=2))
        return

    # Run CLI interview
    assistant = OnboardingAssistant()
    result = assistant.run()
    serializable = {key: serialize(value) for key, value in result.items()}

    if args.json:
        print(json.dumps(serializable, indent=2))
    else:
        print("\n=== Onboarding Plan ===")
        for step in serializable["plan"]:
            print(step)
        print("\n=== Recommendation Details ===")
        for entry in serializable["recommendations"]:
            print(json.dumps(entry, indent=2))
        print("\nIRS EIN Portal:\n", serializable["irs_ein_url"])


if __name__ == "__main__":
    main()
