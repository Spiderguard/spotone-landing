#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
: "${SPOTONE_RELEASE_TOOL:?Configure the release validator before running this command}"
if [[ ! -f "$SPOTONE_RELEASE_TOOL" ]]; then
  echo "Release validator not found." >&2
  exit 2
fi
exec python3 "$SPOTONE_RELEASE_TOOL" --repo "$PWD" "$@"
