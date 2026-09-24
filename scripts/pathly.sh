#!/usr/bin/env sh
# Thin shell wrapper around scripts/pathly_cli.py for GitLab CI components.
# Docs: https://pathlyhq.com/en/developers
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:$PYTHONPATH}"

COMMAND=${1:-ping}
shift || true

exec python3 "${SCRIPT_DIR}/pathly_cli.py" "${COMMAND}" "$@"
