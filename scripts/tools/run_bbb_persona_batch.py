"""
Run Bland batch calls using the BBB persona and a CSV lead sheet.

Usage:
  python3 scripts/tools/run_bbb_persona_batch.py --csv okc_edmond_bland_batch.csv

Required environment variables:
  BLAND_API_KEY
  BBB_PERSONA_ID

Optional environment variables:
  BLAND_FROM_NUMBER
  BLAND_WEBHOOK_URL
  BLAND_BATCH_SIZE (default 50)
  BLAND_MAX_DURATION_MINUTES (default 8)
  BLAND_BATCH_LABEL_PREFIX (default "BBB Persona Batch")
  BLAND_RECORD_CALLS (default true)
  BLAND_WAIT_FOR_GREETING (default true)
  BLAND_DEFAULT_LANGUAGE (default en-US)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from typing import Any, Dict, Iterable, List

import requests


BLAND_BATCH_ENDPOINT = "https://api.bland.ai/v1/batches"


def _to_bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _required_env(name: str) -> str:
    value = _env(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def read_leads(csv_path: str) -> List[Dict[str, str]]:
    leads: List[Dict[str, str]] = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            phone = (row.get("phone_number") or row.get("phone") or "").strip()
            if not phone:
                continue
            leads.append({k: (v or "").strip() for k, v in row.items()})
    return leads


def _request_data(lead: Dict[str, str]) -> Dict[str, Any]:
    full_name = " ".join(
        token for token in [lead.get("first_name", ""), lead.get("last_name", "")] if token
    ).strip()
    return {
        "first_name": lead.get("first_name", ""),
        "last_name": lead.get("last_name", ""),
        "homeowner_name": full_name,
        "property_address": lead.get("property_address", ""),
        "city": lead.get("city", ""),
        "state": lead.get("state", ""),
        "zip_code": lead.get("zip_code", ""),
        "hail_date": lead.get("hail_date", ""),
        "storm_date": lead.get("hail_date", ""),
        "hail_size": lead.get("hail_size", ""),
        "storm_type": lead.get("storm_type", ""),
        "damage_probability": lead.get("damage_probability", ""),
        "structures_hit": lead.get("structures_hit", ""),
        "image_findings": lead.get("image_findings", ""),
        "lead_priority": lead.get("lead_priority", ""),
        "callback_number": lead.get("phone_number", ""),
    }


def _analysis_schema() -> Dict[str, Any]:
    # Keep schema simple and strict enough for post-call automation.
    return {
        "type": "object",
        "properties": {
            "lead_priority": {"type": "string"},
            "homeowner_name": {"type": "string"},
            "property_address": {"type": "string"},
            "callback_number": {"type": "string"},
            "inspection_booked": {"type": "boolean"},
            "preferred_inspection_time": {"type": "string"},
            "call_outcome": {"type": "string"},
            "notes": {"type": "string"},
        },
        "required": [
            "lead_priority",
            "inspection_booked",
            "call_outcome",
            "notes",
        ],
    }


def _call_payload(
    lead: Dict[str, str],
    *,
    persona_id: str,
    webhook: str,
    from_number: str,
    language: str,
    max_duration: int,
    record: bool,
    wait_for_greeting: bool,
) -> Dict[str, Any]:
    phone = lead.get("phone_number") or lead.get("phone") or ""
    payload = {
        "phone_number": phone,
        "persona_id": persona_id,
        "webhook": webhook,
        "request_data": _request_data(lead),
        "analysis_schema": _analysis_schema(),
        "max_duration": max_duration,
        "record": record,
        "wait_for_greeting": wait_for_greeting,
        "language": language,
        "metadata": {
            "lead_source": lead.get("source", "csv_batch"),
            "campaign": lead.get("campaign", ""),
            "city": lead.get("city", ""),
            "state": lead.get("state", ""),
            "property_address": lead.get("property_address", ""),
        },
    }
    if from_number:
        payload["from"] = from_number
    return payload


def chunked(items: List[Dict[str, str]], size: int) -> Iterable[List[Dict[str, str]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def send_batch(
    *,
    bland_api_key: str,
    call_data: List[Dict[str, Any]],
    label: str,
) -> Dict[str, Any]:
    response = requests.post(
        BLAND_BATCH_ENDPOINT,
        headers={
            "Authorization": bland_api_key,
            "Content-Type": "application/json",
        },
        json={"label": label, "call_data": call_data},
        timeout=45,
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Bland batch calls with BBB persona.")
    parser.add_argument("--csv", required=True, help="Path to CSV lead sheet")
    parser.add_argument("--sleep-seconds", type=float, default=2.0, help="Pause between batches")
    args = parser.parse_args()

    try:
        bland_api_key = _required_env("BLAND_API_KEY")
        persona_id = _required_env("BBB_PERSONA_ID")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    from_number = _env("BLAND_FROM_NUMBER")
    webhook = _env("BLAND_WEBHOOK_URL")
    if not webhook:
        print("Missing BLAND_WEBHOOK_URL", file=sys.stderr)
        return 2

    batch_size = int(_env("BLAND_BATCH_SIZE", "50"))
    max_duration = int(_env("BLAND_MAX_DURATION_MINUTES", "8"))
    label_prefix = _env("BLAND_BATCH_LABEL_PREFIX", "BBB Persona Batch")
    language = _env("BLAND_DEFAULT_LANGUAGE", "en-US")
    record_calls = _to_bool(os.getenv("BLAND_RECORD_CALLS"), True)
    wait_for_greeting = _to_bool(os.getenv("BLAND_WAIT_FOR_GREETING"), True)

    leads = read_leads(args.csv)
    if not leads:
        print(f"No callable leads found in {args.csv}", file=sys.stderr)
        return 1

    print(f"Loaded {len(leads)} leads from {args.csv}")
    total_batches = (len(leads) + batch_size - 1) // batch_size

    for idx, leads_batch in enumerate(chunked(leads, batch_size), start=1):
        call_data = [
            _call_payload(
                lead,
                persona_id=persona_id,
                webhook=webhook,
                from_number=from_number,
                language=language,
                max_duration=max_duration,
                record=record_calls,
                wait_for_greeting=wait_for_greeting,
            )
            for lead in leads_batch
        ]
        label = f"{label_prefix} {time.strftime('%Y-%m-%d %H:%M:%S')} #{idx}/{total_batches}"
        print(f"\nSending batch {idx}/{total_batches} ({len(call_data)} calls)")

        try:
            result = send_batch(bland_api_key=bland_api_key, call_data=call_data, label=label)
            print(json.dumps(result, indent=2))
        except Exception as exc:
            print(f"Batch {idx} failed: {exc}", file=sys.stderr)
            return 1

        if idx < total_batches:
            time.sleep(max(0, args.sleep_seconds))

    print("\nAll batches submitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
