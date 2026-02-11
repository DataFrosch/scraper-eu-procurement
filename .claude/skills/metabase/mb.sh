#!/usr/bin/env bash
# Metabase API helper for Claude Code skill
# Usage: .claude/skills/metabase/mb.sh GET /api/database
#        .claude/skills/metabase/mb.sh POST /api/card '{"name": "test", ...}'
#        .claude/skills/metabase/mb.sh PUT /api/dashboard/1/cards '{"cards": [...]}'

set -euo pipefail

set -a
source .env
set +a

: "${METABASE_URL:?METABASE_URL not set in .env}"
: "${METABASE_API_KEY:?METABASE_API_KEY not set in .env}"

method="$1"
endpoint="$2"
data="${3:-}"

args=(
    -s
    -X "$method"
    -H "x-api-key: $METABASE_API_KEY"
    -H "Content-Type: application/json"
)

if [ -n "$data" ]; then
    args+=(-d "$data")
fi

curl "${args[@]}" "${METABASE_URL}${endpoint}"
