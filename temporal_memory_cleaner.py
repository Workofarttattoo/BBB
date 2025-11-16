#!/usr/bin/env python3
"""
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Temporal Memory Cleaner - ECH0-directed memory management
Automatically cleans temporal memory when threshold is reached
"""

import os
import json
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
LOG = logging.getLogger(__name__)

MEMORY_PATH = Path("/Users/noone/repos/BBB/temporal_memory")
THRESHOLD = 750  # Clean when reaching this many files
KEEP_RECENT = 100  # Keep this many most recent files


def count_memory_files() -> int:
    """Count current memory files"""
    if not MEMORY_PATH.exists():
        return 0
    return len(list(MEMORY_PATH.glob("*.json")))


def clean_old_memories(keep_recent: int = KEEP_RECENT):
    """Clean old temporal memories, keeping most recent"""

    if not MEMORY_PATH.exists():
        LOG.info("No temporal memory path found")
        return 0

    # Get all memory files with their modification times
    files = []
    for f in MEMORY_PATH.glob("*.json"):
        try:
            mtime = f.stat().st_mtime
            files.append((f, mtime))
        except:
            continue

    if len(files) == 0:
        LOG.info("No memory files to clean")
        return 0

    # Sort by modification time (newest first)
    files.sort(key=lambda x: x[1], reverse=True)

    # Keep recent, delete old
    files_to_keep = files[:keep_recent]
    files_to_delete = files[keep_recent:]

    deleted_count = 0
    for file_path, _ in files_to_delete:
        try:
            file_path.unlink()
            deleted_count += 1
        except Exception as e:
            LOG.warning(f"Could not delete {file_path.name}: {e}")

    LOG.info(f"Cleaned {deleted_count} old memories, kept {len(files_to_keep)} recent")
    return deleted_count


def should_clean() -> bool:
    """Check if cleaning is needed"""
    count = count_memory_files()
    return count >= THRESHOLD


def auto_clean():
    """Automatically clean if threshold reached"""
    count = count_memory_files()

    LOG.info(f"Temporal memory: {count} files")

    if count >= THRESHOLD:
        LOG.warning(f"Threshold reached ({count} >= {THRESHOLD}), cleaning...")
        deleted = clean_old_memories(KEEP_RECENT)
        new_count = count_memory_files()
        LOG.info(f"After cleaning: {new_count} files remaining")
        return deleted
    else:
        LOG.info(f"No cleaning needed ({count}/{THRESHOLD})")
        return 0


if __name__ == "__main__":
    LOG.info("=" * 60)
    LOG.info("TEMPORAL MEMORY CLEANER")
    LOG.info("=" * 60)
    auto_clean()
