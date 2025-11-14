"""CLI runner for Chief Enhancements meta-agent.

Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SUITE_ROOT = BASE_DIR.parent

# Add parent directory to path for imports
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

# Try relative import first, fall back to absolute
try:
    from chief_enhancements_office.meta_agent import ChiefEnhancementsMetaAgent
except ImportError:
    from meta_agent import ChiefEnhancementsMetaAgent


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for Chief Enhancements meta-agent."""
    parser = argparse.ArgumentParser(
        description="Chief Enhancements meta-agent for product improvement analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run enhancement analysis
  echo '{"product": "My Application"}' | python runner.py

  # Run with demo data
  python runner.py --demo

  # Run with verbose output
  python runner.py --verbose --demo

  # Specify custom output directory
  python runner.py --output-dir ./custom_reports --demo
        """
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with demo data (no stdin required)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Custom output directory for reports"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format only (suppress logs)"
    )

    args = parser.parse_args(argv)

    # Handle demo mode
    if args.demo:
        payload = {
            "product": "Demo Product Enhancement Analysis",
            "options": {
                "analyze_telemetry": True,
                "generate_tickets": True
            }
        }
        if args.verbose and not args.json:
            print("[info] Running in demo mode with example product", file=sys.stderr)
    else:
        try:
            payload = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            error_result = {"status": "error", "message": f"Invalid JSON payload: {exc}"}
            print(json.dumps(error_result))
            return 1

    product = payload.get("product")
    if not product:
        error_result = {"status": "error", "message": "Product name is required"}
        print(json.dumps(error_result))
        return 1

    options = payload.get("options") or {}

    # Setup output directory
    output_dir = args.output_dir or (BASE_DIR / "reports")

    if args.verbose and not args.json:
        print(f"[info] Initializing Chief Enhancements meta-agent", file=sys.stderr)
        print(f"[info] Product: {product}", file=sys.stderr)
        print(f"[info] Output directory: {output_dir}", file=sys.stderr)

    # Initialize and run agent
    try:
        agent = ChiefEnhancementsMetaAgent(knowledge_dir=output_dir)
        ctx = agent.run(product, **options)

        # Build result
        result = {
            "status": "ok",
            "product": ctx.product,
            "telemetry": ctx.telemetry,
            "improvements": ctx.improvements,
            "tickets": ctx.tickets,
            "logs": ctx.logs if args.verbose else [],
        }

        if args.verbose and not args.json:
            print(f"[info] Enhancement analysis completed successfully", file=sys.stderr)
            print(f"[info] Improvements identified: {len(ctx.improvements)}", file=sys.stderr)
            print(f"[info] Tickets generated: {len(ctx.tickets)}", file=sys.stderr)

        print(json.dumps(result, indent=2 if args.verbose else None))
        return 0

    except Exception as exc:
        error_result = {
            "status": "error",
            "message": str(exc),
            "product": product
        }
        print(json.dumps(error_result))
        return 1


def health_check() -> dict:
    """Health check for Chief Enhancements meta-agent."""
    import time
    start = time.time()

    try:
        # Check if we can initialize the agent
        agent = ChiefEnhancementsMetaAgent()

        latency_ms = (time.time() - start) * 1000

        return {
            "tool": "chief_enhancements_office",
            "status": "ok",
            "summary": "Chief Enhancements meta-agent operational",
            "details": {
                "latency_ms": round(latency_ms, 2),
                "knowledge_dir": str(agent.knowledge_dir)
            }
        }
    except Exception as exc:
        latency_ms = (time.time() - start) * 1000
        return {
            "tool": "chief_enhancements_office",
            "status": "error",
            "summary": f"Chief Enhancements meta-agent initialization failed: {exc}",
            "details": {
                "error": str(exc),
                "latency_ms": round(latency_ms, 2)
            }
        }


if __name__ == "__main__":
    sys.exit(main())
