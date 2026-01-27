# Cleanup Guide

This project runs in Docker (`hetzner-web` container) and writes runtime state to files on disk.

## Keep (do not delete)

- `main.py`
- `automation/`
- `static/`
- `docs/`
- `scripts/`
- `requirements.txt`
- `docker-compose.yml`
- `Dockerfile`
- `config.yaml`
- `web_config.json`
- `report_state.json` (web report history / charts)
- `threshold_state.json` (alert threshold state)

## Optional cleanup (safe to delete when needed)

- `__pycache__/` (Python bytecode cache)
- `automation/__pycache__/` (Python bytecode cache)
- `*.bak.*` (backup files, e.g. `report_state.json.bak.*`, `web_config.json.bak.*`)
- `report_state_backups/` (old backups; delete only if you do not need history)

## Notes

- Deleting `report_state.json` resets web history; charts will restart from the next snapshots.
- Deleting `threshold_state.json` resets alert thresholds to 0; the next check will rebuild thresholds.
- If you clean optional files, the system will continue to run normally.

