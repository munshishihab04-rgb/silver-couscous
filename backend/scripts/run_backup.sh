#!/usr/bin/env bash
set -euo pipefail
cd /home/hermesguest/workspace/Licenzpol-definitivamente
backend/.venv/bin/python backend/scripts/backup_mongodb.py >/dev/null
