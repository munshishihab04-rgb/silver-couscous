"""In-process daily encrypted backup scheduler for single-instance deployments."""
from __future__ import annotations

import asyncio
import logging

from scripts.backup_mongodb import create_backup

log = logging.getLogger("licenzpol.backup")


async def daily_backup_loop(interval_seconds: int = 86400) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            result = await create_backup()
            log.info(
                "encrypted backup complete collections=%s documents=%s bytes=%s",
                result["collections"], result["documents"], result["bytes"],
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.error("encrypted backup failed (%s)", type(exc).__name__)
