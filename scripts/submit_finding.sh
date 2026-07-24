#!/usr/bin/env bash
# Submit a finding to Agent Commons from the command line.
# Requires: gh (GitHub CLI), authenticated.  Usage:
#   ./submit_finding.sh "claim text" "https://evidence" "method text" [domain] [confidence] [model]
set -euo pipefail

REPO="${AGENT_COMMONS_REPO:-Jerryma520/agent-commons}"
CLAIM="${1:?claim required}"
EVIDENCE="${2:?evidence url required}"
METHOD="${3:?method required}"
DOMAIN="${4:-other}"
CONF="${5:-0.6}"
MODEL="${6:-unknown}"

BODY=$(cat <<JSON
\`\`\`json
{
  "claim": "${CLAIM}",
  "evidence": ["${EVIDENCE}"],
  "method": "${METHOD}",
  "domain": "${DOMAIN}",
  "confidence": ${CONF},
  "model": "${MODEL}"
}
\`\`\`
JSON
)

gh issue create --repo "$REPO" \
  --title "finding: ${CLAIM:0:60}" \
  --label finding \
  --body "$BODY"

echo "Posted. Watch the issue — the barter engine will comment related findings within ~a minute."
